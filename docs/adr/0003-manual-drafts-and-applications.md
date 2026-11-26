# ADR 0003: Rascunhos imutáveis e acompanhamento manual

- **Status:** Aceita
- **Contexto:** Uma aprovação deve valer somente para uma ação e para o conteúdo exato
  revisado. O envio permanece responsabilidade humana.
- **Decisão:** Persistir cada edição como nova revisão imutável. Hash inclui o conteúdo e
  o vínculo de cada afirmação a fatos confirmados. Aprovações são anexadas à revisão,
  hash e ação; decisões sucessivas recebem sequência transacional.
- **Candidaturas:** Uma candidatura por oportunidade. Transições válidas são aplicadas
  no domínio; o evento é gravado na mesma transação. Marcar `sent` exige confirmação
  humana explícita, sem executar qualquer envio externo.
- **Dados de teste:** Integração usa PostgreSQL e volume isolados do banco local, com
  conteúdo sintético.
