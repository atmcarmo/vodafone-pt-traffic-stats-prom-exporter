Prometheus exporter that gets traffic statistics for Vodafone Portugal HG8247X6-8N WIFI 6 router and exposes them for Prometheus to scrape it.

This is intended for portuguese users so I'll start explaining it in Portugal. You can find the english version down below.

The following metrics are exported:
- `vodafone_wan_up_bytes_total`: total bytes uploaded/transmited for WAN (internet)
- `vodafone_wan_down_bytes_total`: total bytes downloaded/recieved for WAN (internet)
- `vodafone_lan<X>_up_bytes_total`: where `<X>` can be LAN1-LAN4. Total bytes uploaded/transmitted
- `vodafone_lan<X>_up_bytes_total`: where `<X>` can be LAN1-LAN4. Total bytes downloaded/recieved
- `vodafone_wifi_2_4ghz_down_bytes_total`: total bytes downloaded/recieved for Wifi 2.4GHz
- `vodafone_wifi_2_4ghz_up_bytes_total`: total bytes uploaded/transmited for Wifi 2.4GHz
- `vodafone_wifi_5ghz_down_bytes_total`: total bytes downloaded/recieved for Wifi 5GHz
- `vodafone_wifi_5ghz_up_bytes_total`: total bytes uploaded/transmited for Wifi 5GHz

Includes an example with Grafana and Prometheus where you can see your metrics in a dashboard

![Dashboard](https://i.ibb.co/rspgLP5/Screenshot-2022-03-21-at-00-20-11.png)

# Português

## Descrição

Isto é um Prometheus Exporter que recolhe métricas com estatísticas de tráfego e as expõe pare o Prometheus as consiga ler. O objectivo é ser depois visto em dashboards do Grafana (por exemplo).

Recolhe métricas de:
- WAN
- LAN1, LAN2, LAN3, LAN4
- Wifi 2.4GHz e Wifi 5GHz
- Upstream/Downstream

## Como foi testado

Apenas foi testado com a versão de firmware V5R020C10S124. Não é garantido que funcione com qualquer outra versão ou qualquer outro router da operadora.

Testado em macOS e Linux Debian em arquitectura ARM. Não foi testado o uso em Windows

## Requisitos

Ter docker e docker compose instalados.

## Como Utilizar

Criar um ficheiro `.env` equivalente a `.env.example` com as configurações. As seguintes variáveis estão disponíveis:
- `ROUTER_HOST`: IP do Router
- `ROUTER_USERNAME`: username do router
- `ROUTER_PASSWORD`: password do router em plain text (don't worry, não sai da vossa máquina)
- `POLLING_INTERVAL_SECONDS`: o tempo de intervalo em que o exporter vai buscar os dados ao router. Este valor não deve ser baixo para não estarmos a fazer uma espécie de DDoS ao router. Fazer login no router pode aumentar ligeiramente a latência de resposta do router. Recomendo não usar menos do que 60 segundos.
- `EXPORTER_PORT`: a porta onde o exporter expõe as métricas (by default 8081)

 Depois executar `docker-compose up -d`. As métricas podem ser consultadas manualmente ou lidas pelo Prometheus em `<ip>:8081`. Exemplo: `127.0.0.1:8081`.

## Problemas

 Um dos problemas é o contador da WAN/internet usar um `int` de 32 bits. Este `int` é reset para 0 quando atinge o max int. Como este exporter vai buscar os dados com polling significa que podemos perder dados quando o contador faz reset. Infelizmente o router não parece guardar um multiplicador como faz para a as portas LAN e Wifi. Foi adicionado uma lógica que tenta adivinhar quando o contador foi restaurado para 0 e incrementa um multiplicador. Quando é detectado que o actual valor é inferior ao anterior quer quer dizer que o contador foi reiniciado e então é incrementado esse multiplicador. Isto pode ter dois problemas:
 - Se a ligação foi rápida o suficiente o contador pode ser restaurado mais do que uma vez (se forem downloaded muitos dados num curto espaço de tempo) e é impossível saber isso. A única solução é baixar o tempo de polling (o que desaconselho ser menos de 30 segundos)
 - Se por algum motivo o contador for manualmente reiniciado na UI ou se o router sofrer algum bug ou for reiniciado isso pode ser interpretado como um aumento de cerca de 4GB de dados (o multiplicador é incrementado).

 Para desactivar este multipliacdor é possível usar no `.env` a opção `DISABLE_WAN_MULTIPLER=true`.

 ## Solução integrada de monitorização com Grafana e Prometheus

Para efeitos de exemplo foi adicionado um exemplo com Grafana e Prometheus. O Prometheus guarda os dados do exporter e o Grafana tem um dashboard que mostra esses dados para mais fácil visualização. Para efeitos de exemplo foi assumido que a VBox está ligada na porta LAN3 (que foi excluída de alguns gráficos).

Para lançar a solução completa usar o seguinte comando:
`docker-compose -f docker-compose.dashboard.yml up -d`

É possível aceder depois ao dashboard no seguinte endereço: 
`http://<ip>:3000/d/statistics/vodafone-statistics`

![Dashboard](https://i.ibb.co/rspgLP5/Screenshot-2022-03-21-at-00-20-11.png)

## Trabalho futuro:

- Adicionar outras métricas como uptime, número de dispositivos ligados, entre outras.

# English

## Description

This is a Prometheus Exporter that gathers traffic statistics and exposes them as metrics to Prometheus. The goal is to show them in Grafana.

These metrics are being collected and exposed:
- WAN
- LAN1, LAN2, LAN3, LAN4
- Wifi 2.4GHz and 5GHz
- Downstream and upstream

## How was it tested

Only tested with firmware version V5R020C10S124.

Developed and tested with macOS and Linux Debian for ARM architecture.

# How to use

Create a `.env` file similar to `.env.example` with the required information, like username and password. Then run `docker-compose up -d`. Metrics can be found at `<ip>:8081`.

# Future Work

- Have a Grafana dashboard. I already have it but need extra work on automatic the dashboard creation.
- Gather more metrics like uptime, devices, and so on.