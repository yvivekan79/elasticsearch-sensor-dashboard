{pkgs}: {
  deps = [
    pkgs.docker-compose
    pkgs.docker
    pkgs.curl
    pkgs.jq
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
