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
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
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
      flake-parts,
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
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

      # Generate GitHub Actions matrix from checks
      flake.githubActions = inputs.nix-github-actions.lib.mkGithubMatrix {
        inherit (inputs.self) checks;
      };

      perSystem =
        {
          config,
          pkgs,
          lib,
          system,
          ...
        }:
        let
          # Load workspace from pyproject.toml and uv.lock
          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

          # Create overlay for production builds (prefer wheels)
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };

          # Create overlay for development with editable installs
          editableOverlay = workspace.mkEditablePyprojectOverlay {
            root = "$REPO_ROOT";
          };

          # Python interpreter
          python = pkgs.python312;

          # Build base Python package set
          basePythonSet = pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          };

          # Production Python set with locked dependencies
          pythonSet = basePythonSet.overrideScope (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              overlay
            ]
          );

          # Development Python set with editable installs
          devPythonSet = pythonSet.overrideScope (
            lib.composeManyExtensions [
              editableOverlay
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
            ]
          );

          devEnv = devPythonSet.mkVirtualEnv "beautysh-dev-env" workspace.deps.all;
        in
        {
          # Packages exposed by the flake
          packages = {
            default = pythonSet.mkVirtualEnv "beautysh-env" workspace.deps.default;
            beautysh = config.packages.default;
          };

          # Development shell
          devShells.default = pkgs.mkShell {
            packages = [
              devEnv
              pkgs.uv
            ];

            env = {
              # Prevent uv from managing the Python environment
              UV_NO_SYNC = "1";
              UV_PYTHON = devPythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

              # Install pre-commit hooks
              ${config.pre-commit.installationScript}
            '';

            inputsFrom = [
              config.treefmt.build.devShell
              config.pre-commit.devShell
            ];
          };

          # Formatting configuration with treefmt-nix
          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              ruff = {
                enable = true;
                format = true;
              };
              nixfmt = {
                enable = true;
                package = pkgs.nixfmt-rfc-style;
              };
              yamlfmt.enable = true;
              mdformat.enable = true;
            };
          };

          pre-commit.settings = {
            hooks = {
              treefmt.enable = true;
              ruff = {
                enable = true;
                entry = lib.mkForce "${devEnv}/bin/ruff check";
              };
              mypy = {
                enable = true;
                entry = lib.mkForce "${devEnv}/bin/mypy";
              };
              pytest = {
                enable = true;
                entry = lib.mkForce "${devEnv}/bin/pytest";
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
                  entry = "${devEnv}/bin/vermin --eval-annotations --backport argparse --backport dataclasses --backport enum --backport typing --target=${min-python} --violations -vv ./beautysh";
                  pass_filenames = false;
                };
            };
          };
        };
    };
}
