# ADR 0002: Ollama local e bloqueio seguro da Fase 3

- **Status:** Aceita, com avaliação bloqueada
- **Decisão:** Usar Ollama local como provedor candidato. Exigir `OLLAMA_MODEL`
  explicitamente e não definir um modelo padrão.
- **Segurança:** Não fazer chamadas reais até a rubrica, retenção e consentimento serem
  confirmados. Solicitações de avaliação persistem estado `blocked` e não são
  apresentadas como pontuação concluída.
- **Rubrica:** Corte confirmado em 65/100. Pesos confirmados: obrigatório 50,
  desejável 30 e experiência 20.
- **Retenção:** Trechos enviados ao modelo podem ser excluídos após a resposta.
- **Modelo:** Ollama local `llama3.2:3b`.
- **Orçamento:** Sem chamadas reais até aprovação explícita do orçamento.
- **Consequências:** O contrato e o adaptador Ollama podem ser testados por fixture
  sanitizada, mas avaliação real permanece indisponível até novas decisões humanas.
