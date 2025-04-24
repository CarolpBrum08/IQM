## 📂 Como obter os dados necessários

Este aplicativo requer dois arquivos locais para funcionar corretamente:

### 📊 1. Planilha de Indicadores IQM (`IQM_BRASIL_2025.xlsm`)
A planilha completa com os dados por microrregião está disponível apenas para uso interno. Você pode solicitá-la diretamente com a equipe responsável pelo IQM ou colocá-la manualmente no mesmo diretório do projeto.

📍 **Nome do arquivo esperado:** `IQM_BRASIL_2025.xlsm`  
📍 **Local:** Diretório raiz do projeto (mesmo nível do arquivo `IQM_Dashboard_v2.py`)

---

### 🌍 2. Shapefile das Microrregiões do Brasil (`BR_Microrregioes_2022`)
O shapefile completo é automaticamente baixado do Google Drive ao rodar o aplicativo.

📦 **Conteúdo:** Arquivo ZIP contendo `.shp`, `.dbf`, `.shx`, e demais arquivos necessários  
🌐 **Fonte:** Google Drive (ID: `14TwF5uPra8XssUfwwKGiSPdJY4vkTHGT`)  
🔄 **Download automático:** já incluído no código do app via `requests` + `zipfile`

Você **não precisa se preocupar** com o download manual — o app faz isso por você na primeira execução. 😉

[🔗 Link direto para o shapefile no Google Drive](https://drive.google.com/uc?export=download&id=14TwF5uPra8XssUfwwKGiSPdJY4vkTHGT)
