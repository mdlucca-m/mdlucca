"""Config de teste: libera o gate de licenca (MDLUCCA_DEV) para os testes que
exercitam os endpoints, sem depender de um arquivo de licenca no ambiente.
O teste de licenciamento (test_licensing.py) sobrescreve isto quando precisa."""
import os

os.environ.setdefault("MDLUCCA_DEV", "1")
