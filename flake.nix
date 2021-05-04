{
  description = "beautysh";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        flake-utils.follows = "flake-utils";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs = { nixpkgs, flake-utils, poetry2nix, self }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; overlays = [ poetry2nix.overlay ]; };
      projectDir = ./.;
    in
    {
      defaultApp = self.apps.${system}.beautysh;
      defaultPackage = self.packages.${system}.beautysh;

      apps.beautysh = {
        type = "app";
        program = "${self.packages.${system}.beautysh}/bin/beautysh";
      };

      packages.beautysh = pkgs.poetry2nix.mkPoetryApplication {
        inherit projectDir;

        checkPhase = ''
          pytest
        '';
      };

      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          (pkgs.poetry2nix.mkPoetryEnv { inherit projectDir; })

          nix-linter
          nixpkgs-fmt
          poetry
          pre-commit
        ];

        PYTHONPATH = ./src;
      };
    });
}
