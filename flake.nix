{
  description = "procmux";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    pyproject-nix = {
      url = "github:nix-community/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:adisbladis/uv2nix";
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
  };

  outputs = { self, systems, nixpkgs, pyproject-nix, uv2nix
    , pyproject-build-systems, ... }:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
      pkgsFor = forEachSystem (system: import nixpkgs { inherit system; });

      inherit (nixpkgs) lib;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel"; # or sourcePreference = "sdist";
      };

      pyprojectOverrides = _final: _prev: { };

      python = forEachSystem (system: pkgsFor.${system}.python39);

      pythonSets = forEachSystem (system:
        (pkgsFor.${system}.callPackage pyproject-nix.build.packages {
          python = python.${system};
        }).overrideScope (lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
          pyprojectOverrides
        ]));
    in {
      formatter = forEachSystem (system: pkgsFor.${system}.alejandra);

      devShells = forEachSystem (system: {
        default = let
          editableOverlay =
            workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; };
          editablePythonSets = pythonSets.${system}.overrideScope
            (lib.composeManyExtensions [
              editableOverlay

              (final: prev: {
                procmux = prev.procmux.overrideAttrs (old: {
                  src = lib.fileset.toSource {
                    root = old.src;
                    fileset = lib.fileset.unions (map (file: old.src + file) [
                      "/pyproject.toml"
                      # "/README.md"
                      "/procmux"
                    ]);
                  };
                  nativeBuildInputs = old.nativeBuildInputs
                    ++ final.resolveBuildSystem { editables = [ ]; };
                });
              })
            ]);

          virtualenv =
            editablePythonSets.mkVirtualEnv "procmux" workspace.deps.all;
        in pkgsFor.${system}.mkShell {
          packages = with pkgsFor.${system}; [ uv virtualenv ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${virtualenv}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)
          '';
        };
      });

      packages = forEachSystem (system: {
        default =
          pythonSets.${system}.mkVirtualEnv "procmux" workspace.deps.default;
      });

      apps = forEachSystem (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/procmux";
        };
      });
    };
}
