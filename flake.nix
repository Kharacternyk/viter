{
  outputs = { self, nixpkgs }:
    let pkgs = nixpkgs.legacyPackages.x86_64-linux; in {
    devShell.x86_64-linux = pkgs.mkShell {
      buildInputs = with pkgs; [
        vte
        gtk3
        gobject-introspection
        (python3.withPackages(pkgs: with pkgs; [
          pygobject3
        ]))
      ];
    };
  };
}
