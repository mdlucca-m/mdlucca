#!/usr/bin/env Rscript
# scripts/migrate.R — aplica sql/schema.sql à biblioteca SQLite.
#
# O schema é gerado por scripts/gerar_schema.py a partir de
# scripts/busca/deposito.py, que é a fonte única do DDL.

suppressPackageStartupMessages({
  library(DBI)
  library(RSQLite)
  library(glue)
  library(here)
})

migrar <- function(db_file = NULL, schema_file = NULL) {
  proj_root <- here::here()
  data_dir <- file.path(proj_root, "data")
  dir.create(data_dir, showWarnings = FALSE, recursive = TRUE)

  if (is.null(db_file)) db_file <- file.path(data_dir, "db.sqlite")
  if (is.null(schema_file)) schema_file <- file.path(proj_root, "sql", "schema.sql")

  if (!file.exists(schema_file)) {
    stop(glue("schema.sql nao encontrado em: {schema_file}"))
  }

  if (file.exists(db_file)) {
    timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
    bak <- paste0(db_file, ".bak_", timestamp)
    if (!file.copy(db_file, bak, overwrite = TRUE)) {
      stop(glue("Falha ao criar backup em {bak}; abortando antes de alterar o banco."))
    }
    message("Backup criado: ", bak)
  }

  con <- dbConnect(RSQLite::SQLite(), db_file)
  # on.exit so difere a execucao ate o fim de uma funcao; por isso toda a
  # migracao vive dentro de migrar(), e nao no nivel superior do script.
  on.exit(try(dbDisconnect(con), silent = TRUE), add = TRUE)

  message("Lendo schema: ", schema_file)
  sql_text <- paste(readLines(schema_file, warn = FALSE), collapse = "\n")

  # O separador por ";" nao entende blocos BEGIN ... END; (gatilhos), que
  # ficariam partidos ao meio e aplicados errado. Melhor falhar explicitamente.
  if (grepl("\\bBEGIN\\b", sql_text, ignore.case = TRUE)) {
    stop("schema.sql contem bloco BEGIN...END; este aplicador divide por ';' e nao o trata.")
  }

  raw_stmts <- unlist(strsplit(sql_text, "(?<=;)", perl = TRUE))

  # Remover linhas de comentario ANTES de decidir se a instrucao esta vazia.
  # Sem isto, um "-- comentario" grudado no inicio do bloco fazia a instrucao
  # seguinte ser descartada em silencio, deixando tabelas por criar.
  sem_comentario <- gsub("(?m)^[[:space:]]*--[^\n]*$", "", raw_stmts, perl = TRUE)
  stmts <- trimws(sem_comentario)
  stmts <- stmts[nzchar(gsub("[;[:space:]]", "", stmts))]

  message("Statements encontradas: ", length(stmts))

  dbExecute(con, "BEGIN")
  ok <- FALSE
  on.exit({
    if (!ok) try(dbExecute(con, "ROLLBACK"), silent = TRUE)
  }, add = TRUE, after = FALSE)

  for (i in seq_along(stmts)) {
    s <- stmts[[i]]
    message(glue("[{i}/{length(stmts)}] {substr(gsub('[[:space:]]+', ' ', s), 1, 90)}"))
    res <- tryCatch({
      DBI::dbExecute(con, s)
      TRUE
    }, error = function(e) e)
    if (inherits(res, "error")) {
      stop(glue("Erro na statement {i}: {conditionMessage(res)}\nInicio: {substr(s, 1, 400)}"))
    }
  }

  dbExecute(con, "COMMIT")
  ok <- TRUE
  message("Schema aplicado com sucesso (", length(stmts), " statements).")
  invisible(db_file)
}

if (sys.nframe() == 0L) {
  args <- commandArgs(trailingOnly = TRUE)
  migrar(
    db_file = if (length(args) >= 1) args[[1]] else NULL,
    schema_file = if (length(args) >= 2) args[[2]] else NULL
  )
}
