# GPTPar – Gravador de Macros para Navegadores

O GPTPar é um aplicativo desktop que observa cliques e digitação realizados no Firefox, armazena essa interação como uma macro e permite reproduzi-la automaticamente quantas vezes você quiser. A solução foi desenvolvida em Python seguindo os princípios de **código limpo**, **POO** e **Arquitetura Limpa**, utilizando Selenium para automatizar o navegador.

O projeto utiliza o repositório [A9T9/RPA](https://github.com/A9T9/RPA) como referência conceitual para a organização das camadas de captura e reprodução de ações.

## Principais recursos

- Interface gráfica (Tkinter) com botões para gravar, parar, reproduzir, excluir e atualizar macros.
- Gravação de cliques, mudanças em campos e textos digitados com Selenium + Firefox.
- Reexecução automática dos passos registrados, incluindo seleção de opções, preenchimento de campos e mudança de estado de checkboxes.
- Armazenamento das macros em arquivo JSON no diretório do usuário (`~/.gptpar/macros.json`).
- Arquitetura limpa dividindo domínio, casos de uso, infraestrutura e interface.
- Executor dedicado (`executor.py`) para inicializar facilmente a aplicação.

## Arquitetura

```
src/gptpar/
├── domain              # Entidades e contratos (Macro, MacroStep, repositórios, serviços)
├── infrastructure      # Implementações concretas (Selenium, JSON)
├── interface           # Interface gráfica Tkinter
└── usecases            # Casos de uso que orquestram as camadas
```

Cada camada depende apenas de contratos definidos em níveis superiores, permitindo a troca de tecnologias (por exemplo, outro navegador) sem impacto na regra de negócio.

## Pré-requisitos

1. **Python 3.10+**
2. **Firefox** instalado.
3. **Geckodriver** compatível com a versão do Firefox disponível no `PATH` do sistema. Consulte a [documentação oficial](https://firefox-source-docs.mozilla.org/testing/geckodriver/) para download.
4. (Opcional) Ambiente virtual Python para isolar dependências.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Execução

Inicie a interface gráfica com:

```bash
python executor.py
```

Passos básicos:

1. Informe a URL inicial e um nome para a macro.
2. Clique em **Iniciar Gravação** e execute as ações desejadas na janela do Firefox aberta pelo Selenium.
3. Clique em **Finalizar e Salvar** para armazenar o fluxo.
4. Selecione uma macro na lista e use **Reproduzir Macro** sempre que precisar repetir o processo.

## Testes

Para rodar os testes automatizados (não dependem do Selenium), execute:

```bash
pytest
```

## Observações

- O arquivo `~/.gptpar/macros.json` é criado automaticamente na primeira execução para armazenar as macros gravadas.
- Durante a gravação e reprodução o Firefox deve permanecer visível (modo não headless) para que o usuário acompanhe ou interaja conforme necessário.
- Logs informativos são impressos no console para facilitar o diagnóstico de problemas.

## Licença

Este projeto segue a mesma licença do repositório base de referência (MIT).
