{
  description = "A Bash beautifier for the masses";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    git-hooks-nix = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nix-github-actions = {
      url = "github:nix-community/nix-github-actions";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      flake-parts,
      pyproject-build-systems,
      pyproject-nix,
      uv2nix,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.treefmt-nix.flakeModule
        inputs.git-hooks-nix.flakeModule
      ];

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      flake.githubActions = inputs.nix-github-actions.lib.mkGithubMatrix {
        inherit (self) checks;
      };

      perSystem =
        {
          self',
          config,
          pkgs,
          lib,
          ...
        }:
        let
          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };
          editableOverlay = lib.composeManyExtensions [
            (workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; })
            # Fix for hatchling needing editables when building editable packages
            (final: prev: {
              beautysh = prev.beautysh.overrideAttrs (old: {
                nativeBuildInputs =
                  (old.nativeBuildInputs or [ ])
                  ++ final.resolveBuildSystem {
                    editables = [ ];
                  };
              });
            })
          ];
          mkPythonSet =
            python:
            (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
              lib.composeManyExtensions [
                pyproject-build-systems.overlays.wheel
                overlay
              ]
            );

          python = pkgs.python312;
          pythonSet = mkPythonSet python;
          devPythonSet = pythonSet.overrideScope editableOverlay;

          inherit (pkgs.callPackage pyproject-nix.build.util { }) mkApplication;

          venv = pythonSet.mkVirtualEnv "beautysh" workspace.deps.default;
          devVenv = devPythonSet.mkVirtualEnv "beautysh-dev" workspace.deps.all;
          # Non-editable venv with dev deps for sandboxed checks (devVenv's
          # editable overlay points at $REPO_ROOT which doesn't exist here).
          testVenv = pythonSet.mkVirtualEnv "beautysh-test" workspace.deps.all;

          # Run the test suite against a given interpreter. Used for the
          # Python version matrix — vermin catches syntax incompatibilities,
          # but not stdlib/regex behaviour differences across versions.
          mkTestCheck =
            python:
            let
              ps = mkPythonSet python;
              venv = ps.mkVirtualEnv "beautysh-test-${python.pythonVersion}" workspace.deps.all;
            in
            pkgs.runCommand "beautysh-tests-${python.pythonVersion}"
              {
                nativeBuildInputs = [ venv ];
              }
              ''
                cp -r ${self} src
                chmod -R u+w src
                cd src
                pytest
                touch $out
              '';
        in
        {
          checks = {
            inherit (self'.packages) beautysh dist;
            coverage =
              pkgs.runCommand "beautysh-coverage"
                {
                  nativeBuildInputs = [ testVenv ];
                }
                ''
                  cp -r ${self} src
                  chmod -R u+w src
                  cd src
                  mkdir $out
                  pytest --cov --cov-report=xml:$out/coverage.xml --cov-report=term
                '';
            tests-py39 = mkTestCheck pkgs.python39;
            tests-py311 = mkTestCheck pkgs.python311;
            tests-py313 = mkTestCheck pkgs.python313;
          };

          packages = {
            default = self'.packages.beautysh;
            beautysh = mkApplication {
              inherit venv;
              package = pythonSet.beautysh;
            };
            dist =
              let
                distFor =
                  uvBuildType:
                  (pythonSet.beautysh.overrideAttrs (old: {
                    outputs = [
                      "out"
                      "dist"
                    ];
                    env = (old.env or { }) // {
                      inherit uvBuildType;
                    };
                  })).dist;
                wheel = distFor "wheel";
                sdist = distFor "sdist";
              in
              pkgs.symlinkJoin {
                name = "beautysh-dist";
                paths = [
                  wheel
                  sdist
                ];
              };
          };

          devShells.default = pkgs.mkShell {
            packages = [
              devVenv
            ]
            ++ (builtins.attrValues config.treefmt.build.programs)
            ++ config.pre-commit.settings.enabledPackages;

            env = {
              # Prevent uv from managing the Python environment
              UV_NO_SYNC = "1";
              UV_PYTHON = devPythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              unset PYTHONPATH
              # pytestCheckHook leaks this via setupHook; it blocks pytest-cov etc from loading
              unset PYTEST_DISABLE_PLUGIN_AUTOLOAD
              export REPO_ROOT="$(git rev-parse --show-toplevel)"
              ${config.pre-commit.installationScript}
            '';
          };

          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              ruff = {
                enable = true;
                format = true;
              };
              nixfmt.enable = true;
              yamlfmt.enable = true;
              mdformat.enable = true;
            };
          };

          pre-commit.settings = {
            hooks = {
              actionlint.enable = true;
              treefmt.enable = true;
              convco.enable = true;
              ripsecrets.enable = true;
              check-added-large-files.enable = true;
              check-merge-conflicts.enable = true;
              end-of-file-fixer.enable = true;
              trim-trailing-whitespace.enable = true;
              deadnix.enable = true;
              nil.enable = true;
              statix.enable = true;
              ruff = {
                enable = true;
                entry = lib.mkForce "${devVenv}/bin/ruff check";
              };
              mypy = {
                enable = true;
                entry = lib.mkForce "${devVenv}/bin/mypy beautysh/";
                pass_filenames = false;
              };
              pytest = {
                enable = true;
                entry = lib.mkForce "${devVenv}/bin/pytest";
                pass_filenames = false;
              };
              uv-lock = {
                enable = true;
                entry = "${devVenv}/bin/uv lock --check --offline --python '${devPythonSet.python.interpreter}' --no-python-downloads";
                pass_filenames = false;
              };
              vermin =
                let
                  pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
                  inherit (pyproject.project) requires-python;
                  min-python = lib.trim (lib.removePrefix ">=" requires-python);
                in
                {
                  enable = true;
                  entry = "${devVenv}/bin/vermin --eval-annotations --backport argparse --backport dataclasses --backport enum --backport typing --target=${min-python} --violations -vv ./beautysh";
                  pass_filenames = false;
                };
            };
          };
        };
    };
}
