{
  description = "procmux flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        pythonPackages = python.pkgs;

        venvDir = "./venv";

        pythonApp = pythonPackages.buildPythonApplication {
          pname = "procmux";
          version = "0.1.0";
          src = ./.;
          nativeBuildInputs = [ pythonPackages.pip pythonPackages.virtualenv ];
          format = "other";
          buildInputs = [ pythonPackages.setuptools ];

          buildPhase = ''
            virtualenv ${venvDir}
            source ${venvDir}/bin/activate
            pip install -r requirements.txt
            pip install -e .
          '';

          installPhase = ''
            mkdir -p $out/bin
            cp -r ${venvDir} $out/
            echo "#!/bin/sh" > $out/bin/procmux
            echo "source $out/${venvDir}/bin/activate" >> $out/bin/procmux
            echo "exec python -m procmux \"\$@\"" >> $out/bin/procmux
            chmod +x $out/bin/procmux
          '';
        };
      in {
        packages = { default = pythonApp; };

        apps.default = {
          type = "app";
          program = "${pythonApp}/bin/procmux";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pythonPackages.pip
            pythonPackages.virtualenv
            # Add any other development tools you need
          ];

          shellHook = ''
            # Use the same virtualenv as in the build
            source ${venvDir}/bin/activate
            # The application is already installed in editable mode during the build
          '';
        };
      });
}
