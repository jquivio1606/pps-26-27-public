# Comparativa de costes de despliegue: Render vs. Azure vs. AWS vs. Google Cloud

- **Proyecto:** Cinema API (FastAPI + React/Vite + PostgreSQL)
- **Fecha de consulta de precios:** 16/11/2026
- **Moneda:** euros (€), IVA **no** incluido · Tipo de cambio aplicado: **1 € = 1,10 USD**
- **Alcance:** coste mensual de mantener la aplicación en producción, con 1 instancia mínima y sin alta disponibilidad (salvo en el escenario C).

---

## 1. Resumen ejecutivo

La aplicación es **un único servicio web** (FastAPI sirve la API y el frontend ya compilado desde `frontend/dist`) más **una base de datos PostgreSQL**. No necesita CDN propio, colas, almacenamiento de objetos ni contenedores múltiples.

Con esa arquitectura, los costes reales son mucho más bajos de lo que sugieren las calculadoras cuando se dejan los valores por defecto (instancias medianas, 24/7, Multi-AZ y almacenamiento sobredimensionado).

| Proveedor | A. Mínimo viable | B. Equivalente (1 vCPU / 2 GB) | C. Con alta disponibilidad | B en €/año | Región en España |
|---|---:|---:|---:|---:|:---:|
| **Render** | **13,86 €** | 50,50 € | 90,50 € | 606 € | ❌ (Frankfurt) |
| **Azure** | **28,83 €** | **28,83 €** | 53,73 € | **346 €** | ✅ Spain Central |
| **AWS** | 27,27 € | 63,28 € | 126,57 € | 759 € | ✅ eu-south-2 |
| **Google Cloud** | **12,18 €** | 52,60 € | 98,07 € | 631 € | ✅ Madrid |

> Precios de tarifa (sin descuentos por compromiso, sin planes de soporte, sin IVA). Variación esperada: **±10 %** según horas del mes, región exacta y redondeos del proveedor.

**Conclusiones rápidas:**

1. **Lo más barato para este proyecto es Google Cloud con escalado a cero (≈ 12 €/mes)** o **Render con planes de pago mínimos (≈ 14 €/mes)**. Ambos aceptan arranques en frío.
2. **La mejor relación coste/estabilidad es Azure (≈ 29 €/mes)**: región en España, sin arranques en frío, PostgreSQL gestionado y SLA del 99,95 % desde el plan Basic. Es el único caso en el que el escenario "mínimo" y el "equivalente" cuestan lo mismo, porque el plan B1 ya cubre la carga.
3. **AWS es la opción más cara en el escenario equivalente y la más incómoda**: App Runner (la opción "sencilla") **no está disponible en eu-south-2 (España)** y **dejó de aceptar clientes nuevos el 30/04/2026**. La alternativa barata (Lightsail) limita la red privada con la base de datos.
4. **La estimación de Azure (199,15 €) y la de AWS (165,75 €) no son comparables** con las demás: corresponden a SKUs muy superiores (Standard/General Purpose, Multi-AZ, 24/7 e IVA). La de Google Cloud (53,25 €) sí es coherente. Ver [§7](#7-reconciliación-con-tus-estimaciones).
5. **El despliegue actual en Render gratuito no es una opción de producción**: el servicio web se suspende por inactividad y **PostgreSQL gratuito caduca a los 30 días** (con 14 días de gracia antes de borrarse).

---

## 2. Qué se compara exactamente

### 2.1. Carga de referencia

| Parámetro | Valor usado | Comentario |
|---|---|---|
| Peticiones | 500.000 / mes | ≈ 16.400/día; muy holgado para un proyecto académico |
| Latencia media | 200 ms | Determina el consumo en proveedores por petición (Cloud Run) |
| CPU / RAM | 1 vCPU / 2 GB | "Equivalente" a las calculadoras |
| Instancias | 1 (mínimo), 24/7 en B | Sin autoescalado |
| PostgreSQL | 32 GB SSD, Single-AZ | 20–32 GB es el rango típico de las calculadoras |
| Salida a Internet | 20 GB / mes | Imágenes, JSON, estáticos |
| Horas de facturación | 730 h/mes | 365 días × 24 h / 12 |

### 2.2. Escenarios

| Escenario | Qué incluye | Para quién |
|---|---|---|
| **A. Mínimo viable** | 0,5 vCPU / 512 MB–1 GB, 1 instancia, PostgreSQL pequeño (10–40 GB), sin HA. Puede haber arranque en frío. | Producción real de este proyecto, presupuesto mínimo |
| **B. Equivalente** | 1 vCPU / 2 GB, 24/7, PostgreSQL 32 GB, Single-AZ, 20 GB de salida. | Comparación "manzana con manzana" con las calculadoras |
| **C. Con HA** | 2 instancias de aplicación + base de datos Multi-AZ / zone-redundant. | Solo si se exige continuidad del servicio |

### 2.3. Lo que **no** se ha incluido

- IVA (21 % en España). Si eres particular o no puedes deducirlo, **multiplica por 1,21**.
- Planes de soporte (Azure Support, AWS Business, Google Cloud Support).
- Instancias reservadas, Savings Plans, compromisos de 1–3 años o *spot*.
- Backups externos, WAF, balanceadores adicionales, monitorización de pago.
- Créditos de bienvenida (Azure 200 $, AWS credits, GCP 300 $): son puntuales, no recurrentes.
- Dominio y certificados (incluidos o gratuitos en los cuatro proveedores).

### 2.4. Dimensionado real del proyecto (importante)

La base de datos de esta aplicación ocupa **unos pocos MB**, no 32 GB. Con 500.000 peticiones/mes y 20 GB de salida se está siendo ya muy conservador: por eso el escenario **A** es la referencia de coste real, y el **B** solo sirve para comparar con las calculadoras.

Además, Azure impone **32 GiB mínimos** de almacenamiento en PostgreSQL Flexible Server y Cloud SQL impone **10 GB mínimos**: son suelos de facturación, no necesidades del proyecto.

---

## 3. Tabla comparativa principal

### 3.1. Coste mensual (€, sin IVA)

| Concepto | Render | Azure | AWS | Google Cloud |
|---|---:|---:|---:|---:|
| Cómputo de aplicación (A) | 6,36 € | 11,83 € | 13,64 € | 0,00 € |
| Base de datos (A) | 5,45 € | 13,07 € | 13,64 € | 7,73 € |
| Almacenamiento y backups (A) | 0,00 € | 3,93 € | 0,00 € | 2,27 € |
| Salida a Internet (A) | 2,05 € | 0,00 € | 0,00 € | 2,18 € |
| **Total A (mínimo viable)** | **13,86 €** | **28,83 €** | **27,27 €** | **12,18 €** |
| **Total B (equivalente)** | **50,50 €** | **28,83 €** | **63,28 €** | **52,60 €** |
| **Total C (con HA)** | **90,50 €** | **53,73 €** | **126,57 €** | **98,07 €** |

> En el escenario A de Google Cloud se asume **escalado a cero**; en Render, plan Starter (0,5 CPU); en AWS, Lightsail; en Azure no hay plan más barato que B1 + B1ms.

### 3.2. Coste anual del escenario B

| Proveedor | €/mes | €/año | Índice (Azure = 100) |
|---|---:|---:|---:|
| Azure | 28,83 € | 346 € | 100 |
| Render | 50,50 € | 606 € | 175 |
| Google Cloud | 52,60 € | 631 € | 182 |
| AWS | 63,28 € | 759 € | 220 |

### 3.3. Lectura de la tabla

- **Azure gana en el escenario B** porque B1 (1 vCPU / 1,75 GB) y B1ms (1 vCore / 2 GiB) son exactamente el tamaño necesario, y la salida hasta 100 GB/mes es gratuita.
- **Render no tiene un plan de 1 vCPU barato**: para 1 CPU hay que ir a Standard (25 $) y la base de datos de 1 GB cuesta 19 $.
- **AWS paga el peaje de su modelo**: contenedor gestionado + RDS + almacenamiento. Su opción barata (Lightsail) limita la red privada con RDS.
- **Google Cloud** solo es barato si se acepta escalar a cero; con una instancia mínima encendida 24/7, el tiempo inactivo se factura y se acerca a Render.

---

## 4. Desglose por proveedor

### 4.1. Render (Frankfurt, USD → €)

Planes vigentes: web **Starter 7 $** (0,5 CPU / 512 MB), **Standard 25 $** (1 CPU / 2 GB); PostgreSQL **Basic-256mb 6 $**, **Basic-1GB 19 $**, almacenamiento adicional **0,30 $/GB-mes**; *workspace* Hobby con **5 GB** de tráfico incluido y **0,15 $/GB** adicional.

**Escenario B (equivalente):**

| Concepto | SKU / tarifa | Cantidad | USD/mes | €/mes |
|---|---|---:|---:|---:|
| Web service | Standard (1 CPU / 2 GB) | 1 | 25,00 | 22,73 |
| PostgreSQL | Basic-1GB | 1 | 19,00 | 17,27 |
| Almacenamiento | 31 GB adicionales × 0,30 $ | 31 | 9,30 | 8,45 |
| Salida | 15 GB sobre los 5 incluidos × 0,15 $ | 15 | 2,25 | 2,05 |
| **Total** | | | **55,55** | **50,50** |

**Escenario A (mínimo viable):** Starter 7 $ + Basic-256mb 6 $ + 15 GB de salida (2,25 $) = **15,25 $ ≈ 13,86 €**.

**Escenario C (HA):** dos instancias Standard (50 $) + PostgreSQL con réplica (≈ 2 × 19 $) + almacenamiento + salida = **99,55 $ ≈ 90,50 €**.

> **Notas**
> - Se asume que el plan de PostgreSQL incluye 1 GB de almacenamiento. Si Render factura desde el primer GB, suma 0,30 $/mes (≈ 0,27 €): irrelevante.
> - Se usa el *workspace* **Hobby** (gratuito). Para producción con equipo, el plan **Pro** cuesta **25$/mes** adicionales; a cambio incluye 25 GB de tráfico, con lo que el escenario B subiría a ≈ 78 $ ≈ **71€/mes**.
> - El plan gratuito de web service **se suspende a los 15 minutos de inactividad** y el PostgreSQL gratuito **caduca a los 30 días**. No sirve como producción.
> - Render no tiene región en España; Frankfurt es la más cercana (≈ 30–40 ms desde la península).

### 4.2. Azure (Spain Central, EUR)

Precios de la API pública de precios de Azure para **spaincentral** (16/11/2026):

| Recurso | SKU | Tarifa | €/mes |
|---|---|---|---:|
| App Service Linux | **B1** (1 vCPU / 1,75 GB) | 0,0162 €/h × 730 h | 11,83 |
| PostgreSQL Flexible | **B1ms** (1 vCore / 2 GiB) | 0,0179 €/h × 730 h | 13,07 |
| Almacenamiento | 32 GiB (mínimo) × 0,1229 €/GiB | 32 | 3,93 |
| Backup | LRS, gratis hasta el 100 % de lo aprovisionado | — | 0,00 |
| Salida | 20 GB (primeros 100 GB gratis) | 20 | 0,00 |
| **Total B** | | | **28,83** |

**Escenario A:** idéntico a B. No existe un plan más barato que B1 + B1ms con PostgreSQL Flexible, y el almacenamiento mínimo son 32 GiB.

**Escenario C (HA):** 2 × B1 (23,66 €) + PostgreSQL con standby zone-redundant, ≈ 2 × B1ms (26,14 €) + almacenamiento (3,93 €) = **53,73 €**. Si se activan backups zone-redundant, añade ≈ 3,9 €/mes.

> **Notas**
> - **B1 sí tiene SLA del 99,95 %**, pero no incluye autoescalado ni *deployment slots*. Si los necesitas, valora S1 (62,27 €/mes) o P0v3 (58,33 €/mes).
> - **Elegir Windows en lugar de Linux multiplica el coste**: B1 Windows cuesta 0,0673 €/h (≈ 49,13 €/mes) frente a 0,0162 €/h en Linux.
> - **No hace falta Static Web Apps**: FastAPI sirve el frontend. Si se separara, SWA Standard añadiría ≈ 8 €/mes.
> - Azure es, junto con AWS (eu-south-2), uno de los dos proveedores con **región en la península**; su catálogo de precios es el más simple de los cuatro para este caso.

### 4.3. AWS (eu-south-2, USD → €)

AWS no tiene una opción "PaaS sencilla" equivalente a las demás:

- **App Runner** exige **2 GB mínimo** con 1 vCPU, **no está en eu-south-2** y **no acepta clientes nuevos desde el 30/04/2026** (AWS recomienda ECS Express Mode).
- **ECS Fargate + ALB** funciona, pero el balanceador y las IPv4 públicas encarecen mucho un servicio pequeño.
- **Lightsail Containers** es la opción barata y predecible, pero sin integración directa con la VPC de RDS.

**Escenario B (Lightsail + RDS):**

| Concepto | SKU / tarifa | Cantidad | USD/mes | €/mes |
|---|---|---:|---:|---:|
| Contenedor | Lightsail **Medium** (1 vCPU / 2 GB) | 1 | 40,00 | 36,36 |
| PostgreSQL | RDS **db.t4g.small** Single-AZ, 0,035 $/h | 730 h | 25,55 | 23,23 |
| Almacenamiento | gp3 32 GB × 0,127 $ | 32 | 4,06 | 3,69 |
| Salida | 500 GB incluidos en Lightsail | 20 GB | 0,00 | 0,00 |
| **Total** | | | **69,61** | **63,28** |

**Alternativa con ECS Fargate (más "AWS nativo"):** Fargate 1 vCPU / 2 GB ≈ 41,50 $ + ALB ≈ 20,74 $ + IPv4 pública ≈ 3,65 $ + RDS 25,55 $ + gp3 4,06 $ = **95,50 $ ≈ 86,82 €/mes**.

**Escenario A (mínimo viable):** Lightsail **Small** (0,5 vCPU / 1 GB) 15 $ + Lightsail Managed Database PostgreSQL 15 $ = **30 $ ≈ 27,27 €**. Con RDS en su lugar: db.t4g.micro ≈ 12,41 $ + 20 GB gp3 2,54 $ + contenedor 15 $ ≈ **29,95 $ ≈ 27,23 €**.

**Escenario C (HA):** 2 nodos Medium (80 $) + RDS **Multi-AZ** (2 × 25,55 $) + gp3 duplicado (8,13 $) = **139,23 $ ≈ 126,57 €**.

> **Notas**
> - **Lightsail no se integra directamente con la VPC de RDS**: la conexión va por el endpoint público con TLS. Funciona, pero añade latencia y superficie de exposición. Si eso no es aceptable, hay que ir a Fargate + ALB (+23 €/mes).
> - **RDS Multi-AZ duplica el coste de la base de datos** y también el almacenamiento.
> - **100 GB/mes de salida gratuitos**; el resto, ≈ 0,09 $/GB.
> - **Amplify** solo sería necesario si se separara el frontend (≈ 0,75–2 $/mes por build, almacenamiento y transferencia).

### 4.4. Google Cloud (Madrid / europe-southwest1, USD → €)

Cloud Run en Madrid es **Tier 1**: 0,000024 $/vCPU-s activo, 0,0000025 $/vCPU-s inactivo con instancia mínima, 0,0000025 $/GiB-s de memoria y 0,40 $/millón de peticiones. Nivel gratuito: **180.000 vCPU-s, 360.000 GiB-s y 2 millones de peticiones al mes**.

Con 500.000 peticiones × 0,2 s = **100.000 s de CPU activa** y 200.000 GiB-s, **todo el consumo activo cae dentro del nivel gratuito**. Lo que se paga es la **instancia mínima encendida** el resto del mes.

**Escenario B (equivalente, 1 instancia mínima 1 vCPU / 2 GiB):**

| Concepto | Cálculo | USD/mes | €/mes |
|---|---|---:|---:|
| Cloud Run activo | 100.000 vCPU-s + 200.000 GiB-s + 0,5 M peticiones | 0,00 | 0,00 |
| Cloud Run inactivo (min = 1) | 2.528.000 s × (0,0000025 + 2 × 0,0000025) | 18,96 | 17,24 |
| Cloud SQL PostgreSQL | db-g1-small ≈ 0,039 $/h × 730 h | 28,50 | 25,91 |
| SSD | 32 GB × 0,17 $ | 5,44 | 4,95 |
| Backups | 32 GB × 0,08 $ | 2,56 | 2,33 |
| Salida | 20 GB × 0,12 $ | 2,40 | 2,18 |
| **Total** | | **57,86** | **52,60** |

**Escenario A (escalado a cero):** Cloud Run 0 $ (todo dentro del nivel gratuito) + Cloud SQL **db-f1-micro** ≈ 8,50 $ + 10 GB SSD 1,70 $ + backups 0,80 $ + salida 2,40 $ = **13,40 $ ≈ 12,18 €**.

**Escenario C (HA):** 2 instancias mínimas (37,92 $) + Cloud SQL con **HA** (2 × 28,50 $) + SSD 5,44 $ + backups 5,12 $ + salida 2,40 $ = **107,88 $ ≈ 98,07 €**.

> **Notas**
> - **Con escalado a cero hay arranque en frío** (1–3 s típicos en FastAPI; más si el contenedor es grande).
> - **db-f1-micro y db-g1-small no tienen SLA** y están pensados para desarrollo/pruebas. Para producción, Cloud SQL con vCPU dedicada sube a ≈ 50–60 $/mes.
> - **Cloud SQL exige 10 GB mínimos** de almacenamiento.
> - La salida gratuita de 1 GiB solo aplica en Norteamérica; en Europa se factura desde el primer GB.
> - El frontend puede seguir sirviéndose desde FastAPI; no hace falta Firebase Hosting.

---

## 5. Comparación cualitativa

| Criterio | Render | Azure | AWS | Google Cloud |
|---|---|---|---|---|
| Región en España | ❌ Frankfurt | ✅ Spain Central | ✅ eu-south-2 | ✅ Madrid |
| Arranque en frío (plan barato) | Sí (free) / No (pago) | **No** | No | Sí con min = 0 |
| SLA en el plan más barato | No (Hobby) | **Sí, 99,95 % (B1)** | No (Lightsail) | Cloud Run sí; Cloud SQL *shared-core* no |
| PostgreSQL gestionado | ✅ | ✅ | ✅ | ✅ |
| Red privada app ↔ BD | ✅ | ✅ | ⚠️ limitada en Lightsail | ✅ |
| Precio predecible | ✅ | ✅ | ⚠️ muchos servicios | ⚠️ depende del tráfico |
| Complejidad de despliegue | **Muy baja** | Baja | **Alta** | Media |
| Límite del plan barato | 512 MB RAM, 0,5 CPU | 1,75 GB RAM, sin autoescalado | 1 GB RAM (Lightsail) | 0,6 GB RAM (f1-micro) |
| Riesgo específico | Free caduca a 30 días | Ninguno relevante | App Runner cerrado / fuera de España | Cold starts y SLA |

**Coste de separar el frontend** (si no se sirve desde FastAPI): Render Static Site gratis, Azure SWA Standard ≈ 8 €/mes, AWS Amplify ≈ 1–2 $/mes, Firebase Hosting gratis hasta 10 GB. **En este proyecto no es necesario**.

---

## 6. El despliegue actual (Render gratuito) no es producción

`render.yaml` define hoy un web service `plan: free` en Frankfurt con PostgreSQL externo. Dos límites lo descalifican para producción:

1. **El servicio web se suspende sin tráfico**; la primera petición puede tardar ≈ 1 minuto.
2. **PostgreSQL gratuito caduca a los 30 días** de su creación, con 14 días de gracia antes de borrarse. Pasado ese plazo, la aplicación se queda sin base de datos.

**Salida mínima recomendada:** Starter (7 $) + Basic-256mb (6 $) ≈ **13,86 €/mes**, o bien migrar a Azure B1 + B1ms ≈ **28,83 €/mes** si se quiere región en España y cero arranques en frío.

---

## 7. Reconciliación con tus estimaciones

| Proveedor | Tu estimación | Recalculado (B) | Diferencia | Explicación |
|---|---:|---:|---:|---|
| **Azure** | 199,15 € | 28,83 € | **+590 %** | La estimación corresponde a **App Service S1 + PostgreSQL General Purpose D2ds_v4**, no a B1 + B1ms |
| **AWS** | 165,75 € | 63,28 € | **+162 %** | **24/7 + Multi-AZ + db.t4g.medium + IVA**, y App Runner con 2 GB mínimo |
| **Google Cloud** | 53,25 € | 52,60 € | **+1,2 %** | Coherente: misma arquitectura y supuestos |
| **Render** | — | 50,50 € | — | Equivalente a Standard + Basic-1GB + 32 GB |

### 7.1. Azure: de dónde salen los ≈ 200 €

Reconstrucción con precios de Spain Central:

| Concepto | SKU | €/mes |
|---|---|---:|
| App Service Linux | **S1** (0,0853 €/h × 730 h) | 62,27 |
| PostgreSQL Flexible | **General Purpose D2ds_v4**, 2 vCores (2 × 0,0952 €/h × 730 h) | 139,00 |
| Almacenamiento | 32 GiB × 0,1229 € | 3,93 |
| **Total** | | **205,20** |

Tu cifra (199,15 €) encaja con ese orden de magnitud (por ejemplo, 720 h en lugar de 730 h). **La diferencia no es un error de precio, sino de SKU:** el equivalente real para esta aplicación es **B1 + B1ms (28,83 €)**.

Causas probables, por orden de impacto:

1. **PostgreSQL General Purpose de 2 vCores** en lugar de Burstable B1ms: **+125,93 €/mes**.
2. **App Service Standard S1** en lugar de Basic B1: **+50,44 €/mes**.
3. Si además se eligió **Windows** en lugar de Linux, B1 pasaría de 11,83 € a 49,13 €/mes.
4. Static Web Apps Standard (≈ 8 €/mes) si se separó el frontend.

### 7.2. AWS: de dónde salen los ≈ 166 €

| Concepto | SKU | USD/mes |
|---|---|---:|
| App Runner | 1 vCPU / 2 GB, 24/7 (0,064 $/vCPU-h + 0,007 $/GB-h) | 56,94 |
| RDS PostgreSQL | **db.t4g.medium Multi-AZ** (≈ 0,13 $/h) | 94,90 |
| Almacenamiento | gp3 20 GB × 2 copias × 0,127 $ | 5,08 |
| Amplify | build + almacenamiento + transferencia | 0,75 |
| **Total** | | **157,67** |

Sin IVA: **≈ 143,34 €**; con IVA del 21 %: **≈ 173,44 €**. Tu cifra (165,75 €) cae entre ambas, así que la estimación es internamente consistente, pero **sobredimensionada** para esta aplicación:

- **24/7** cuando el tráfico real no lo exige.
- **Multi-AZ** cuando el escenario de referencia es Single-AZ.
- **db.t4g.medium** (2 vCPU / 4 GB) cuando basta db.t4g.small o micro.
- **App Runner** no está en España y ya no admite clientes nuevos.

### 7.3. Google Cloud: estimación correcta

52,60 € recalculados frente a 53,25 € estimados (1,2 % de diferencia). La estructura de coste es la esperada: Cloud Run con instancia mínima + Cloud SQL db-g1-small + 32 GB + salida. **No hay nada que corregir**, solo confirmar si se quiere pagar la instancia mínima (≈ 17 €/mes) o aceptar arranques en frío (0 €).

---

## 8. Recomendación

| Objetivo | Opción | Coste |
|---|---|---:|
| **Mínimo coste absoluto, con cold starts** | Google Cloud: Cloud Run a cero + Cloud SQL db-f1-micro | **≈ 12 €/mes** |
| **Mínimo coste sin cold starts, despliegue simple** | Render: Starter + Basic-256mb | **≈ 14 €/mes** |
| **Mejor equilibrio (recomendado)** | **Azure: B1 Linux + PostgreSQL B1ms (Spain Central)** | **≈ 29 €/mes** |
| **Si se exige HA** | Azure: 2 × B1 + PostgreSQL zone-redundant | **≈ 54 €/mes** |
| **Evitar** | Render free (caduca), App Runner (cerrado y fuera de España) | — |

**Recomendación razonada:** para la puesta en producción de este proyecto, **Azure B1 + B1ms** es la opción más sensata: está en España, no hay arranques en frío, el precio es el más bajo del escenario equivalente y el despliegue es sencillo (App Service + PostgreSQL Flexible). Si el criterio es exclusivamente el coste y se acepta latencia de arranque, **Cloud Run con escalado a cero** baja a ≈ 12 €/mes.

Si se mantiene Render, **hay que salir del plan gratuito al menos en PostgreSQL** antes de los 30 días. El mínimo razonable es Starter + Basic-256mb (≈ 14 €/mes).

---

## 9. Sensibilidad: qué cambia el resultado

| Cambio | Efecto aproximado |
|---|---|
| Añadir IVA (21 %) | Todos los importes × 1,21 |
| Bajar el almacenamiento a 1–10 GB reales | Render −9 €, AWS −4 €, GCP −5,5 €, Azure −3,6 € (suelo de 32 GiB) |
| Quitar la instancia mínima en Cloud Run | GCP B −17 €/mes (hasta ≈ 35 €) |
| Contratar el *workspace* Pro de Render | +23 €/mes (compensa con 25 GB de tráfico incluidos) |
| Pasar Azure B1 → S1 (autoescalado y *slots*) | +50 €/mes |
| Pasar AWS Single-AZ → Multi-AZ | +26 €/mes (base de datos) y +4 €/mes (almacenamiento) |
| Usar instancias reservadas / Savings Plans 1 año | −20 % a −40 % en cómputo (no aplicable a un proyecto de un curso) |
| Variación del tipo de cambio ±5 % | ±0,6–3 €/mes según proveedor |

---

## 10. Cómo validar estas cifras

1. **Render:** Dashboard → *Billing* → simulador de planes; comprobar si el plan de PostgreSQL incluye 1 GB.
2. **Azure:** [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) con **Linux**, región **Spain Central**, App Service **B1** y PostgreSQL Flexible **B1ms**, 32 GiB, Single-AZ.
3. **AWS:** [AWS Pricing Calculator](https://calculator.aws/) con región **Europe (Spain) eu-south-2**, Lightsail Medium o ECS Fargate 1 vCPU/2 GB, RDS PostgreSQL **db.t4g.small Single-AZ**, 32 GB gp3.
4. **Google Cloud:** [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) con región **europe-southwest1 (Madrid)**, Cloud Run 1 vCPU/2 GiB, **min instances = 1**, Cloud SQL PostgreSQL **db-g1-small**, 32 GB SSD.
5. **Comprobar la factura real del primer mes**: los cuatro proveedores facturan por segundo/hora y los redondeos pueden mover el total un 5–10 %.

---

## 11. Fuentes

Consultadas el **16/11/2026**:

- Render — <https://render.com/pricing> y <https://docs.render.com/free>
- Azure App Service (Linux) — <https://azure.microsoft.com/pricing/details/app-service/linux/>
- Azure Database for PostgreSQL Flexible Server — <https://azure.microsoft.com/pricing/details/postgresql/flexible-server/>
- API pública de precios de Azure (región `spaincentral`) — <https://prices.azure.com/api/retail/prices>
- AWS Lightsail — <https://aws.amazon.com/lightsail/pricing/>
- AWS Fargate — <https://aws.amazon.com/fargate/pricing/>
- Amazon RDS for PostgreSQL — <https://aws.amazon.com/rds/postgresql/pricing/>
- AWS App Runner — <https://aws.amazon.com/apprunner/pricing/>
- Google Cloud Run — <https://cloud.google.com/run/pricing>
- Google Cloud SQL — <https://cloud.google.com/sql/pricing>
- Google Cloud VPC (salida a Internet) — <https://cloud.google.com/vpc/network-pricing>

> Los precios cambian con frecuencia y dependen de la región y del tipo de cuenta. Antes de contratar, confirma el importe en la calculadora oficial con la configuración exacta.

---

## 12. Anexo: fórmulas usadas

```text
Coste mensual (24/7)   = precio_hora × 730
Coste anual            = coste_mensual × 12
Conversión a euros     = importe_USD / 1,10
Con IVA               = importe_sin_IVA × 1,21

Cloud Run (activo)     = peticiones × latencia_s × vCPU × 0,000024
                       + peticiones × latencia_s × GiB × 0,0000025
                       + peticiones / 1.000.000 × 0,40

Cloud Run (mínimo 1)   = (730 × 3600 − segundos_activos)
                       × (0,0000025 × vCPU + 0,0000025 × GiB)

AWS Fargate            = (vCPU × 0,0466 + GiB × 0,00512) × 730
AWS RDS Multi-AZ       = 2 × coste_Single_AZ (cómputo y almacenamiento)

Azure PostgreSQL HA    = 2 × coste_cómputo_B1ms + almacenamiento
```

**Ejemplo comprobado (Google Cloud, escenario B):**

```text
Activo:  100.000 s × 1 vCPU × 0,000024 = 2,40 $
         200.000 GiB-s × 0,0000025      = 0,50 $
         0,5 M peticiones × 0,40         = 0,20 $   → 3,10 $ (dentro del nivel gratuito)
Inactivo: 2.528.000 s × (0,0000025 + 2 × 0,0000025) = 18,96 $
Cloud SQL: 28,50 $ + SSD 5,44 $ + backups 2,56 $ + salida 2,40 $
Total: 57,86 $ ≈ 52,60 €
```
