# LoL Odds — app web (PC + celular), atualiza sozinho

## O que é
Página (`index.html`) que abre no navegador do PC e do celular. Você escolhe 2 times
(e o draft, se quiser), vê % de vitória, odd justa, e compara com a odd da casa.
Os ratings se atualizam sozinhos via GitHub, de madrugada. NÃO precisa editar código.

## Arquivos (suba todos, mantendo a estrutura de pastas)
    index.html
    bundle.js
    update_ratings.py
    SETUP.md
    .github/workflows/daily.yml      <-- precisa ficar nessa pasta

## Passo a passo (uma vez, ~10 min)
1. Crie um repositório PÚBLICO no GitHub (ex.: `lol-odds`).
   (No plano grátis, o Pages e a leitura do ratings.json exigem repo público.)
2. Suba os arquivos. O `daily.yml` vai em `.github/workflows/` — pela web, use
   "Add file > Create new file" e digite o nome `.github/workflows/daily.yml`
   (as barras criam as pastas), depois cole o conteúdo.
3. Settings > Pages > Source = "Deploy from a branch", branch = `main`, pasta `/root`,
   Save. Em ~1 min aparece a URL `https://SEU_USUARIO.github.io/lol-odds/`.
4. Aba Actions > "daily-ratings-update" > Run workflow — roda a 1ª atualização
   na hora (senão só rodaria de madrugada). Isso gera o `ratings.json` no repo.
5. Pronto. Abra a URL do Pages. A página acha o `ratings.json` sozinha.

## No celular
Abra a URL do GitHub Pages e use "Adicionar à tela de início" — vira ícone,
abre em tela cheia como app. Sem instalar nada, sem loja.

## Indicador de status (canto sup. direito)
- verde + data = lendo ratings.json atualizado do GitHub
- amarelo = usando snapshot embutido (arquivo ainda não gerado, ou aberto offline)

## Ressalvas
- 1ª vez: rode o workflow na mão (passo 4), senão o ratings.json só existe após a 1ª madrugada.
- Time com <5 jogos na base aparece com aviso de confiança BAIXA.
- Sem digitar jogadores, o modelo usa Elo de time (leve perda de precisão).
- odd justa = 1/prob. Há valor quando a casa paga ACIMA dela. Não é conselho financeiro.
- Se a Oracle's Elixir mudar a URL do CSV, ajuste em update_ratings.py (variável OE_URL).
