# Reconstrução 3D multi-câmera (Etapa 3)

Hoje o sistema analisa a partir de **uma câmera** (vista sagital) usando os
*world landmarks* do MediaPipe: **ângulos, velocidades e acelerações angulares
são medidas diretas**; a profundidade (eixo Z) é estimada. Com **2–3 câmeras
sincronizadas e calibradas**, cada ponto do corpo passa a ser **triangulado em
3D métrico verdadeiro**, sem assumir plano sagital — melhora força/potência fora
do plano e movimentos com rotação.

O núcleo matemático já está pronto e testado em `app/multicam.py`
(`tests/test_multicam.py`): triangulação linear **DLT** de N vistas, modelo de
câmera `P = K[R|t]`, ponderação por visibilidade e erro de reprojeção.

## Protocolo de captura (3 câmeras)

| Item | Recomendação |
|---|---|
| **Arranjo** | ~120° entre si ao redor do atleta (frontal, oblíqua, lateral); corpo inteiro no enquadramento na fase de maior amplitude. |
| **Sincronização** | Clap/flash comum no início (ou timecode); alinhar no pós pelo evento compartilhado (pico de áudio ou frame do flash). |
| **Calibração** | Tabuleiro de xadrez (ex.: 9×6, quadrado 25 mm) visível em pares de câmeras → intrínsecos (Zhang 2000) + extrínsecos por pose relativa; escala por objeto de dimensão conhecida. |
| **FPS** | ≥ 60 fps para explosivos (idealmente 120–240); **mesma taxa** nas 3 câmeras. |
| **Saída** | Por câmera: landmarks 2D (px) por frame + matriz `P`. O módulo triangula para 3D e alimenta o mesmo pipeline (`kinematics`/`biomech`). |

## Fluxo pretendido

1. `pose_extract.py` roda em **cada** vídeo → landmarks 2D por câmera.
2. Calibrar câmeras (tabuleiro) → `Camera.from_krt(K, R, t)` por câmera.
3. `multicam.triangulate_landmarks(cams, views, vis)` → landmarks 3D métricos.
4. `build_session_from_pose.py` (adaptado p/ 3D triangulado) → sessão no banco.
5. **Todas** as análises e o **laudo padronizado** rodam igual — só que sobre
   3D verdadeiro.

## O que muda no laudo

- **Melhora:** força/potência resultantes (componentes fora do plano), momentos
  articulares em movimentos com rotação, trajetória do CoM em 3D real.
- **Não muda o método:** o `PADRÃO DE ANÁLISE` (grupos, checagens de literatura,
  fadiga) é o mesmo — apenas a fonte dos pontos fica mais precisa.

## Próximos passos de implementação

- [ ] `scripts/calibrate_cameras.py` — intrínsecos/extrínsecos a partir de vídeos
      do tabuleiro (OpenCV `calibrateCamera` + `stereoCalibrate`).
- [ ] `scripts/sync_clips.py` — alinhamento por pico de áudio/flash.
- [ ] `scripts/triangulate_session.py` — orquestra pose(×N) → 3D → bundle.
- [ ] Adaptar `build_session_from_pose.py` para aceitar landmarks já em 3D.
