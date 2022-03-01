Prometheus exporter that gets traffic statistics for Vodafone Portugal HG8247X6-8N WIFI 6 router and exposes them for Prometheus to scrape

This is intended for portuguese users so I'll start explaining it in Portugal. You can find the english version down bellow.

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

Criar um ficheiro `.env` equivalente a `.env.example` com as configurações, incluindo username e password. Depois executar:

`docker-compose up -d`

As métricas podem ser consultadas manualmente ou lidas pelo Prometheus em `<ip>:8081`. Exemplo: `127.0.0.1:8081`.

## Trabalho futuro:

- Disponibilizar, via `docker-compose`, um Prometheus e um Grafana com um dashboard pré-configurado para ser possível visualizar os dados. Já o tenho mas preciso de trabalhar na automação do dashboard do Grafana.
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