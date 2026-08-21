# CFA WLSMV do BRUMS - modelo de 6 fatores, 23 itens (tensao_1 excluido)
# Reproduz os indices de ajuste para a Tabela/paragrafo de qualidade das medidas.
library(lavaan)
dat <- read.csv("brums_itens_anon.csv")
# item morto: ten1 (Apavorado) = 99,6% no piso, variancia ~0 -> excluir
itens_ord <- setdiff(names(dat), "ten1")
dat[itens_ord] <- lapply(dat[itens_ord], ordered)

modelo <- '
  Tensao   =~ ten2 + ten3 + ten4
  Depressao=~ dep1 + dep2 + dep3 + dep4
  Raiva    =~ rai1 + rai2 + rai3 + rai4
  Vigor    =~ vig1 + vig2 + vig3 + vig4
  Fadiga   =~ fad1 + fad2 + fad3 + fad4
  Confusao =~ con1 + con2 + con3 + con4
'
fit <- cfa(modelo, data = dat, ordered = itens_ord, estimator = "WLSMV")
fitMeasures(fit, c("chisq.scaled","df.scaled","pvalue.scaled",
                   "cfi.scaled","tli.scaled","rmsea.scaled","srmr"))
