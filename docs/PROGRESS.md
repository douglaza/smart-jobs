# Progresso

Fase atual: 4
Objetivo: Preparar rascunhos verdadeiros, registrar aprovações vinculadas ao conteúdo
exato e acompanhar candidaturas por ações humanas.

Entregas concluídas:
- Fases 0 a 3: pacote instalável, tooling, CI, API, PostgreSQL, importação manual e
  avaliação bloqueada sem chamadas reais ao LLM até haver orçamento.
- Migrações `20261125_0004` a `20261125_0006`: rascunhos/revisões, aprovações,
  candidaturas/eventos, vínculo afirmação-fato e ordenação de decisões.
- Revisões imutáveis com hash SHA-256 de conteúdo e referências de fatos.
- Cada afirmação do rascunho precisa aparecer no texto e referenciar somente fatos
  existentes e confirmados; inserir fatos requer perfil com consentimento.
- Aprovação vinculada à revisão, hash e ação `manual_application`; conteúdo alterado
  cria nova revisão sem herdar aprovação anterior.
- Máquina de estados de candidatura no domínio, com unicidade por oportunidade.
- Estado e evento são persistidos na mesma transação; transições inválidas são rejeitadas.
- Estado `sent` exige confirmação humana explícita; nenhum envio externo é realizado.
- PostgreSQL de integração usa volume próprio `smart_jobs_test_db`, separado do banco
  local.

Testes e comandos executados:
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy`
- `docker compose config`
- `docker compose --profile test config`
- `docker compose --profile test run --build --rm integration-tests`
- `docker compose --profile test exec db-test psql -U test_user -d smart_jobs_test -Atc 'SELECT count(*) FROM application_events'`
- `docker compose --profile test restart db-test`
- Repetição da consulta SQL de contagem de eventos após reinício
- `uv build`

Evidências da verificação:
- Testes locais: 11 aprovados; 2 integrações isoladas ignoradas sem `DATABASE_URL`.
- Ruff lint/format: aprovados.
- mypy strict: nenhum problema em 18 arquivos de código.
- PostgreSQL isolado: 2 testes de integração aprovados; suíte repetida com sucesso.
- Migrações aplicadas desde banco vazio até `20261125_0006`.
- Fluxo HTTP completo verificado: fato confirmado → rascunho → aprovação → edição →
  aprovação invalidada → nova revisão aprovada → registro manual de envio.
- Fato não confirmado não pode ser usado no rascunho; duplicata de candidatura retorna
  HTTP 409; envio sem confirmação também retorna HTTP 409.
- Histórico consultado pela API após reinício do PostgreSQL; contagem permaneceu em 17
  eventos, incluindo 4 registros com confirmação humana de envio.
- Fixtures de integração contêm apenas dados sintéticos.
- Build de wheel e source distribution concluído com sucesso.
- O teste de integração mostra aviso não bloqueante de depreciação do
  `starlette.testclient` com `httpx`.

Decisões/ADRs:
- [ADR 0001](adr/0001-foundation-and-tooling.md): fundação Python/uv.
- [ADR 0002](adr/0002-local-llm-blocking.md): Ollama local candidato, sem chamadas reais
  até orçamento autorizado.
- [ADR 0003](adr/0003-manual-drafts-and-applications.md): revisões imutáveis e fluxo
  manual com eventos transacionais.

Pendências e limitações:
- Sem geração automática de rascunhos; conteúdo é informado manualmente.
- Não há envio real de candidatura nem integração com plataformas externas.
- Orçamento de chamadas reais ao Ollama segue não autorizado.
- Currículo e fatos reais não foram cadastrados.
- O usuário informou que os commits anteriores foram enviados ao GitHub.

Próxima fase proposta:
- Fase 5: painel pessoal após aprovação explícita.

Aprovação para avançar: aguardando
