{
  description = "USBGuard Waybar Applet - Control USBGuard from Waybar";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pygobject3
          dbus-python
          setuptools
        ]);

        usbg = pkgs.python3Packages.buildPythonApplication {
          pname = "usbg";
          version = "0.1.0";
          
          src = ./.;
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            pygobject3
            dbus-python
          ];
          
          buildInputs = with pkgs; [
            gtk4
            libadwaita
            gobject-introspection
            wrapGAppsHook3
          ];
          
          nativeBuildInputs = with pkgs; [
            gobject-introspection
            wrapGAppsHook3
            python3Packages.setuptools
          ];
          
          dontWrapGApps = true;
          
          makeWrapperArgs = [
            "\${gappsWrapperArgs[@]}"
          ];
          
          format = "pyproject";
        };
        
      in {
        packages = {
          default = usbg;
          usbg = usbg;
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            gtk4
            libadwaita
            gobject-introspection
            usbguard
            pkg-config
            python3Packages.build
            python3Packages.setuptools
            python3Packages.wheel
          ];
          
          shellHook = ''
            export GI_TYPELIB_PATH="${pkgs.gtk4}/lib/girepository-1.0:${pkgs.libadwaita}/lib/girepository-1.0:$GI_TYPELIB_PATH"
            export LD_LIBRARY_PATH="${pkgs.gtk4}/lib:${pkgs.libadwaita}/lib:$LD_LIBRARY_PATH"
            export IN_NIX_SHELL=1
            echo "USBGuard Waybar Applet development environment"
            echo "Run 'python -m usbg' to start the applet"
          '';
        };
        
        checks = {
          build = usbg;
        };
      }
    ) // {
      nixosModules.default = { config, lib, pkgs, ... }:
        with lib;
        let
          cfg = config.services.usbg;
        in {
          options.services.usbg = {
            enable = mkEnableOption "USBGuard Waybar Applet";

            package = mkOption {
              type = types.package;
              default = self.packages.${pkgs.system}.default;
              description = "The USBG package to use.";
            };

            waybar = {
              enable = mkEnableOption "Waybar integration";
              config = mkOption {
                type = types.attrs;
                default = {
                  "custom/usbguard" = {
                    exec = "${cfg.package}/bin/usbg waybar --continuous";
                    return-type = "json";
                    interval = "once";
                    tooltip = true;
                    on-click = "${cfg.package}/bin/usbg gui";
                  };
                };
                description = "Waybar configuration for USBG module.";
              };
            };

            systemdUserService = mkEnableOption "Systemd user service for Waybar";
          };

          config = mkIf cfg.enable {
            # Enable USBGuard
            services.usbguard.enable = true;

            # D-Bus permissions
            environment.etc."dbus-1/system.d/usbguard.conf".text = ''
              <!DOCTYPE busconfig PUBLIC
               "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
               "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
              <busconfig>
                <policy context="default">
                  <allow send_destination="org.usbguard1"/>
                </policy>
              </busconfig>
            '';

            # Install package
            environment.systemPackages = [ cfg.package ];

            # Waybar integration
            programs.waybar = mkIf cfg.waybar.enable {
              enable = true;
              settings = cfg.waybar.config;
            };

            # Systemd user service
            systemd.user.services.usbg-waybar = mkIf cfg.systemdUserService {
              description = "USBGuard Waybar Applet";
              wantedBy = [ "graphical-session.target" ];
              partOf = [ "graphical-session.target" ];
              serviceConfig = {
                ExecStart = "${cfg.package}/bin/usbg waybar --continuous";
                Restart = "always";
              };
            };
          };
        };

      homeManagerModules.default = { config, lib, pkgs, ... }:
        with lib;
        let
          cfg = config.services.usbg;
        in {
          options.services.usbg = {
            enable = mkEnableOption "USBGuard Waybar Applet";

            package = mkOption {
              type = types.package;
              default = self.packages.${pkgs.system}.default;
              description = "The USBG package to use.";
            };

            waybar = {
              enable = mkEnableOption "Waybar integration";
              config = mkOption {
                type = types.attrs;
                default = {
                  "custom/usbguard" = {
                    exec = "${cfg.package}/bin/usbg waybar --continuous";
                    return-type = "json";
                    interval = "once";
                    tooltip = true;
                    on-click = "${cfg.package}/bin/usbg gui";
                  };
                };
                description = "Waybar configuration for USBG module.";
              };
            };

            systemdUserService = mkEnableOption "Systemd user service for Waybar";
          };

          config = mkIf cfg.enable {
            # Install package
            home.packages = [ cfg.package ];

            # Waybar integration
            programs.waybar = mkIf cfg.waybar.enable {
              enable = true;
              settings = cfg.waybar.config;
            };

            # Systemd user service
            systemd.user.services.usbg-waybar = mkIf cfg.systemdUserService {
              Unit = {
                Description = "USBGuard Waybar Applet";
                After = [ "graphical-session.target" ];
                PartOf = [ "graphical-session.target" ];
              };
              Service = {
                ExecStart = "${cfg.package}/bin/usbg waybar --continuous";
                Restart = "always";
              };
              Install = {
                WantedBy = [ "graphical-session.target" ];
              };
            };
          };
        };
    };
}
