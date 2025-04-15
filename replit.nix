{pkgs}: {
  deps = [
    pkgs.curl
    pkgs.jq
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
