# Database Module

## 1. Propósito

Este módulo contiene la definición, organización y puesta en marcha de las estructuras de base de datos del proyecto **Plataforma Distribuida de Conversión Monetaria Interbancaria – ASFI**.

El sistema está compuesto por:

- **14 bases de datos bancarias**, distribuidas en múltiples motores
- **1 base de datos central ASFI**, en motor relacional

Las bases bancarias almacenan las cuentas de clientes y sus saldos en USD cifrados según el algoritmo asignado a cada banco.

La base central ASFI almacena:

- metadata de bancos
- conversiones monetarias
- auditoría del proceso
- inconsistencias detectadas

---

## 2. Estructura del módulo

```text
database/
│
├── schemas/
│   ├── bank_schema.sql
│   ├── asfi_schema.sql
│
├── migrations/
│   └── .gitkeep
│
└── README.md