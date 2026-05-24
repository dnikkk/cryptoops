# CryptoOps DDS Dashboard

Streamlit multipage app: **ДДС (движение денежных средств)** по кошелькам Sepolia.

## Требования

- Python 3.10+
- `ETHERSCAN_API_KEY` в `cryptoops/.env` (обязательно)
- `SEPOLIA_RPC_URL` в `.env` (для страницы «Балансы»)

## Установка

```powershell
cd C:\Users\d_nik\pypro\cryptoops\dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Запуск

```powershell
cd C:\Users\d_nik\pypro\cryptoops\dashboard
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

## Структура

| Путь | Назначение |
|------|------------|
| `app.py` | О проекте (главная) |
| `pages/` | ДДС, Карта потоков, SLA, Балансы |
| `wallets.yaml` | Реестр Safe + EOA |
| `lib/` | Etherscan, классификатор, ДДС DataFrame |
| `cache/{address}/` | Сырой кэш API (локально) |
| `protocol_addrs.yaml` | Известные контракты DeFi (расширяется из tx) |

Спецификация: [`.cursor/prompts/streamlit-dds-dashboard.md`](../.cursor/prompts/streamlit-dds-dashboard.md)

## Утилиты

```powershell
# Прогреть кэш Etherscan для всех 8 адресов реестра
python scripts/warm_cache.py

# Сверить классификацию эталонных tx §3.4
python scripts/validate_classifier.py
```

## Sidebar (ДДС)

- **Safe #1** / **Safe #2** — зелёная кнопка Safe + 3 подписанта Rabby под ней
- Пометка **Deployer** — в колонке `notes` таблицы ДДС (кошелёк Rabby-A #2)
