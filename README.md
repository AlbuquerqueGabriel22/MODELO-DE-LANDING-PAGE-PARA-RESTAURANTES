# Dom do Sabor

Site institucional responsivo para uma churrascaria, desenvolvido com Flask, HTML, CSS e JavaScript.

O projeto apresenta a identidade do restaurante, sua história, o cardápio e os canais de contato.

## Sobre o projeto

Este projeto foi desenvolvido para divulgar a marca Dom do Sabor de forma visual e profissional, com uma experiência responsiva para desktop e mobile. A estrutura utiliza Flask para renderizar as páginas HTML e organiza os arquivos estáticos em pastas separadas para facilitar manutenção e evolução.

## Funcionalidades

- Página inicial com destaque visual e slides automáticos
- Seção “Conheça a casa” com apresentação visual da estrutura e ambiente
- Página “Nossa história” com narrativa e imagens do restaurante
- Página de cardápio com apresentação de pratos e receitas
- Página de contato com e-mail, WhatsApp, Instagram e TikTok
- Layout responsivo para desktop e celular
- Animações de entrada e suporte à redução de movimento

## Tecnologias

- Python 3
- Flask
- HTML5 com templates Jinja
- CSS3
- JavaScript

## Estrutura do projeto

```text
.
├── backend.py
├── README.md
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
├── templates/
│   ├── paginaPrincipal.html
│   ├── restaurante.html
│   ├── pratosReceitas.html
│   └── contato.html
└── .venv/   (criado localmente)
```

## Requisitos

- Python 3.10 ou superior
- pip
- Navegador moderno

## Instalação

No PowerShell, dentro da pasta do projeto, execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Flask
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute o comando abaixo apenas nesta sessão:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Depois, ative novamente o ambiente virtual e continue.

## Executando o projeto

Para iniciar a aplicação:

```powershell
python backend.py
```

Para executar em modo de desenvolvimento com recarregamento automático:

```powershell
python backend.py --debug
```

## Rotas

| Rota           | Página              |
| -------------- | ------------------- |
| `/`            | Página principal    |
| `/restaurante` | Nossa história      |
| `/receitas`    | Cardápio e receitas |
| `/contato`     | Canais de contato   |

## Verificações rápidas

Teste se todas as páginas respondem corretamente:

```powershell
python -c "from backend import backend; client=backend.test_client(); [print(route, client.get(route).status_code) for route in ['/', '/restaurante', '/receitas', '/contato']]"
```

A resposta esperada é `200` para todas as rotas.

Para validar a sintaxe do JavaScript:

```powershell
node --check static/js/script.js
```

## Personalização

- Edite os textos e links nas páginas dentro da pasta `templates/`
- Ajuste cores, tipografia, espaçamento e responsividade em `static/css/style.css`
- Modifique slides, filtros e interações em `static/js/script.js`
- Adicione imagens nas pastas de `static/images/` e referencie-as com `url_for('static', filename='...')`

## Observações

- Os dados de contato atuais são demonstrativos e devem ser substituídos pelos dados reais do restaurante antes da publicação
- O modo `debug` deve ser usado somente durante o desenvolvimento
- Para implantação em produção, recomenda-se configurar variáveis de ambiente e ajustar a segurança da aplicação

## Licença

Este projeto é destinado para uso educacional e institucional. Caso seja utilizado em produção, revise os textos, imagens e informações de contato antes de publicar.
