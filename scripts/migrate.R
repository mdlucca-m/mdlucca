#!/usr/bin/env Rscript
# scripts/migrate.R  (versão fixa: aplica statements individualmente)
suppressPackageStartupMessages({
  library(DBI)
  library(RSQLite)
  library(glue)
  library(here)
})

proj_root <- here::here()
data_dir <- file.path(proj_root, "data")
dir.create(data_dir, showWarnings = FALSE, recursive = TRUE)

db_file <- file.path(data_dir, "db.sqlite")
schema_file <- file.path(proj_root, "sql", "schema.sql")

if (!file.exists(schema_file)) {
  stop(glue("schema.sql não encontrado em: {schema_file}\nCertifique-se de que sql/schema.sql exista."))
}

# backup existing sqlite if exists
if (file.exists(db_file)) {
  timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  bak <- paste0(db_file, ".bak_", timestamp)
  file.copy(db_file, bak, overwrite = TRUE)
  message("Backup criado: ", bak)
}

# create connection
con <- dbConnect(RSQLite::SQLite(), db_file)
# garantimos que a conexão será desconectada ao final
on.exit({
  try(dbDisconnect(con), silent = TRUE)
})

# leitura e aplicação do schema statement a statement
message("Lendo schema: ", schema_file)
sql_text <- paste(readLines(schema_file, warn = FALSE), collapse = "\n")
raw_stmts <- unlist(strsplit(sql_text, "(?<=;)", perl = TRUE))
stmts <- trimws(raw_stmts)
stmts <- stmts[nzchar(stmts)]

message("Statements encontradas: ", length(stmts))
i <- 0L
for (s in stmts) {
  i <- i + 1L
  # pular comentários puros
  if (grepl("^\\s*--", s)) next
  # checar conexão
  if (!dbIsValid(con)) stop(glue("Conexão inválida antes de executar statement {i}. Aborting."))
  message(glue("[{i}/{length(stmts)}] Executing (start): {substr(s,1,120)}"))
  res <- tryCatch({
    DBI::dbExecute(con, s)
    TRUE
  }, error = function(e) {
    e
  })
  if (inherits(res, "error")) {
    stop(glue("Erro ao aplicar schema.sql na statement {i}: {conditionMessage(res)}\nStatement start: {substr(s,1,400)}"))
  }
}
message("Schema aplicado com sucesso (statements individuais).")