let
  nixpkgs = import <nixpkgs> {};
in
  with nixpkgs;
  mkShell {
    name = "beautysh";
    buildInputs = [
      bash
      (
        python3Full.withPackages (
          ps: with ps; [
            flake8
            nose
            python-language-server
            setuptools
            twine
          ]
        )
      )
    ];
  }
