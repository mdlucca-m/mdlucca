# =====================================================================
# Replicação canônica em R — BRUMS × HIIT
# Fecha as análises do Apêndice B com os estimadores de referência:
#   CFA WLSMV (ordinal) + HTMT + invariância -> lavaan / semTools
#   TRI / Modelo de Resposta Graduada        -> mirt
#   Fator de Bayes (one-sample JZS)          -> BayesFactor
#
# A versão em Python (analise_avancada.py) já roda estas análises com motores
# livres (semopy/girth/scipy) e chega às mesmas conclusões. Use este script
# para obter os estimadores canônicos (WLSMV com ajuste média-variância).
#
# Uso:  Rscript replicacao_R.R      (na pasta que contém itens_brums.csv)
# Requer:  install.packages(c("lavaan","semTools","mirt","BayesFactor"))
# =====================================================================

pkgs <- c("lavaan","semTools","mirt","BayesFactor")
faltando <- pkgs[!sapply(pkgs, requireNamespace, quietly = TRUE)]
if (length(faltando)) stop("Instale antes: install.packages(c(",
                           paste(sprintf('\"%s\"', faltando), collapse=", "), "))")
suppressMessages({library(lavaan); library(semTools); library(mirt); library(BayesFactor)})

d <- read.csv("itens_brums.csv", stringsAsFactors = FALSE)
itens <- c(paste0("tensao_",1:4), paste0("depressao_",1:4), paste0("raiva_",1:4),
           paste0("vigor_",1:4), paste0("fadiga_",1:4), paste0("confusao_",1:4))
d[itens] <- lapply(d[itens], function(x) ordered(x))   # ordinais p/ WLSMV

modelo <- '
  Tensao    =~ tensao_1 + tensao_2 + tensao_3 + tensao_4
  Depressao =~ depressao_1 + depressao_2 + depressao_3 + depressao_4
  Raiva     =~ raiva_1 + raiva_2 + raiva_3 + raiva_4
  Vigor     =~ vigor_1 + vigor_2 + vigor_3 + vigor_4
  Fadiga    =~ fadiga_1 + fadiga_2 + fadiga_3 + fadiga_4
  Confusao  =~ confusao_1 + confusao_2 + confusao_3 + confusao_4
'

# ---------- 1) CFA WLSMV ----------
fit <- cfa(modelo, data = d, ordered = itens, estimator = "WLSMV")
cat("\n== CFA (WLSMV) — índices robustos ==\n")
print(fitMeasures(fit, c("chisq.scaled","df.scaled","pvalue.scaled",
                         "cfi.scaled","tli.scaled","rmsea.scaled","srmr")))
cat("\n== Cargas padronizadas ==\n")
print(standardizedSolution(fit)[standardizedSolution(fit)$op == "=~",
                                  c("lhs","rhs","est.std","pvalue")], row.names = FALSE)

# ---------- 2) HTMT (policórico) ----------
cat("\n== HTMT (correlações policóricas) ==\n")
print(round(semTools::htmt(modelo, data = d, ordered = itens), 3))

# ---------- 3) Invariância de medida (pré x pós) ----------
cat("\n== Invariância de medida: pré x pós ==\n")
dm <- d[d$momento %in% c("pre","pos"), ]
cfg <- cfa(modelo, data = dm, group = "momento", ordered = itens, estimator = "WLSMV")
met <- cfa(modelo, data = dm, group = "momento", ordered = itens, estimator = "WLSMV",
           group.equal = "loadings")
sca <- cfa(modelo, data = dm, group = "momento", ordered = itens, estimator = "WLSMV",
           group.equal = c("loadings","thresholds"))
print(compareFit(cfg, met, sca))

# ---------- 4) TRI / GRM (mirt) ----------
cat("\n== TRI: Modelo de Resposta Graduada (discriminação a por item) ==\n")
subescalas <- list(
  Tensao=paste0("tensao_",1:4), Depressao=paste0("depressao_",1:4),
  Raiva=paste0("raiva_",1:4), Vigor=paste0("vigor_",1:4),
  Fadiga=paste0("fadiga_",1:4), Confusao=paste0("confusao_",1:4))
for (s in names(subescalas)) {
  m <- tryCatch(mirt(d[subescalas[[s]]], 1, itemtype = "graded", verbose = FALSE),
                error = function(e) NULL)
  if (!is.null(m)) {
    a <- coef(m, simplify = TRUE)$items[, "a1"]
    cat(sprintf("  %-10s a = %s\n", s, paste(round(a,2), collapse=", ")))
  }
}

# ---------- 5) Fator de Bayes (one-sample JZS) para o Δ agudo ----------
cat("\n== Fator de Bayes (JZS) — Δ agudo pré→pós, agregado por atleta ==\n")
w <- reshape(d[d$momento %in% c("pre","pos"),
               c("atleta","dia","momento","FadFis","esc_vigor","PTH","esc_fadiga","esc_confusao")],
             idvar = c("atleta","dia"), timevar = "momento", direction = "wide")
for (v in c("FadFis","esc_vigor","PTH","esc_fadiga","esc_confusao")) {
  delta <- w[[paste0(v,".pos")]] - w[[paste0(v,".pre")]]
  ag <- tapply(delta, w$atleta, mean, na.rm = TRUE); ag <- ag[is.finite(ag)]
  bf <- extractBF(ttestBF(ag))$bf
  cat(sprintf("  %-12s BF10 = %.3f (n=%d)\n", v, bf, length(ag)))
}
cat("\nConcluído.\n")
