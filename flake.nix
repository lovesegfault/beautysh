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
      inherit (pkgs.lib) attrValues last listToAttrs mapAttrs nameValuePair replaceStrings;
      projectDir = ./.;
      pyVersions = [ "3.7" "3.8" "3.9" ];
      pyLatest = "python${last pyVersions}";
    in
    {
      defaultApp = self.apps.${system}.beautysh;
      defaultPackage = pkgs.linkFarmFromDrvs "beautysh" (attrValues self.packages.${system});

      apps.beautysh = {
        type = "app";
        program = "${self.packages.${system}.${"beautysh-${pyLatest}"}}/bin/beautysh";
      };

      packages = flake-utils.lib.flattenTree (
        let
          pyVersionToNix = v: "python${replaceStrings ["."] [""] v}";
          pyOuts = map
            (v: nameValuePair "beautysh-python${v}" pkgs.${pyVersionToNix v})
            pyVersions;
          mkBeautysh = python: pkgs.poetry2nix.mkPoetryApplication {
            inherit projectDir python;
            checkPhase = "pytest";
          };

        in
        mapAttrs (_: mkBeautysh) (listToAttrs pyOuts)
      );

      devShell =
        let
          beatyshEnv = pkgs.poetry2nix.mkPoetryEnv {
            inherit projectDir;
            editablePackageSources.beautysh = ./beautysh;
          };
        in
        beatyshEnv.env.overrideAttrs (old: {
          nativeBuildInputs = with pkgs; old.nativeBuildInputs ++ [
            nix-linter
            nixpkgs-fmt
            pre-commit
            poetry
            pyright
          ];
        });
    });
}
