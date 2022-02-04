{
  description = "beautysh";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
    utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        flake-utils.follows = "utils";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs = { self, nixpkgs, poetry2nix, utils }:
    let
      inherit (nixpkgs) lib;
      pyVersions = map (v: "python${v}") [ "37" "38" "39" "310" ];
    in
    {
      overlay =
        let
          addBeautysh = pyVer: final: prev: {
            "${pyVer}" = prev.${pyVer}.override {
              packageOverrides = pyFinal: _: {
                beautysh = final.poetry2nix.mkPoetryApplication {
                  inherit (pyFinal) python;
                  projectDir = ./.;
                  checkPhase = "pytest";
                };
              };
            };
            "${pyVer}Packages" = final.${pyVer}.pkgs;
          };
        in
        lib.composeManyExtensions ([ poetry2nix.overlay ] ++ (map addBeautysh pyVersions));
    } // utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
        pyLatest = lib.last pyVersions;
      in
      {
        defaultApp = self.apps.${system}.beautysh;
        defaultPackage = pkgs.linkFarmFromDrvs "beautysh" (lib.attrValues self.packages.${system});
        apps.beautysh = {
          type = "app";
          program = "${self.packages.${system}."beautysh-${pyLatest}"}/bin/beautysh";
        };
        packages =
          let
            fmtName = pyVer: "beautysh-${pyVer}";
            getPkg = pyVer: pkgs.${pyVer}.pkgs.beautysh;
            allVers = map (v: lib.nameValuePair (fmtName v) (getPkg v)) pyVersions;
          in
          lib.listToAttrs allVers;

        devShell =
          let
            beautysh = pkgs.poetry2nix.mkPoetryEnv {
              python = pkgs.${pyLatest};
              projectDir = ./.;
              editablePackageSources.beautysh = ./beautysh;
            };
          in
          beautysh.env.overrideAttrs (old: {
            nativeBuildInputs = with pkgs; old.nativeBuildInputs ++ [
              nix-linter
              nixpkgs-fmt
              poetry
              pre-commit
              pyright
              rnix-lsp
            ];
          });
      });
}
