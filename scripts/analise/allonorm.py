# Allometric normalization by body mass and T-CAR peak velocity (see roc_allo_deriv.py for base allometric fit).
# Computes exponents b for Y=a*X^b (X=mass, PV), raw Spearman with covariates, and normalized Y/X^b.
# Reads hum_prof.csv + app_data.json (athletes); outputs allonorm.json + figura x_allonorm.
# Reproducible companion to build_semana_v4.py section 4.16.
