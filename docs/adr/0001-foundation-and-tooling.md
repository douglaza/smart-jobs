# ADR 0001: Fundação e ferramentas da Fase 0

- **Status:** Aceita
- **Contexto:** O projeto começa vazio e precisa de uma base reproduzível antes de
  implementar domínio ou infraestrutura.
- **Decisão:** Usar Python 3.13.18, uv para ambiente e lockfile, `src/` layout,
  pytest, Ruff e mypy. Usar monólito modular e não introduzir FastAPI, banco,
  Docker, LLM ou automação nesta fase.
- **Compatibilidade:** O Python 3.13 foi instalado e validado pelo ambiente de
  desenvolvimento. As versões finais das ferramentas ficam fixadas pelo `uv.lock`.
- **Consequências:** A primeira validação deve importar o pacote e executar somente
  verificações locais. Funcionalidades futuras exigirão novas decisões e ADRs.
