/**
 * Componentes de visualização para bases de dados de citações em tempo real.
 * Integra OpenAlex, Scopus e Web of Science no painel Ao Vivo.
 */

const BasesUI = {
  /**
   * Monta o painel de citações em tempo real
   */
  montarPainelCitacoes(dados) {
    if (!dados?.resumo) return '';

    const resumo = dados.resumo;
    const linhas = dados.linhas || [];

    return `
      <div class="bases-painel">
        <div class="bases-header">
          <h2>
            <i data-lucide="trending-up"></i>
            Citations in Real Time
          </h2>
          <span class="bases-timestamp">
            <i data-lucide="refresh-cw"></i>
            Updated: ${new Date(dados.gerado_em).toLocaleString()}
          </span>
        </div>

        <div class="bases-resumo">
          <div class="metric-card metric-total">
            <div class="metric-label">Total Citations</div>
            <div class="metric-value">${resumo.total_citacoes.toLocaleString()}</div>
            <div class="metric-meta">${resumo.total_artigos} articles</div>
          </div>

          <div class="metric-card metric-media">
            <div class="metric-label">Avg Citations/Article</div>
            <div class="metric-value">${resumo.media_citacoes.toFixed(1)}</div>
            <div class="metric-meta">from ${resumo.linhas_ativas} research lines</div>
          </div>

          <div class="metric-card metric-fonte">
            <div class="metric-label">Data Source</div>
            <div class="metric-fonte-list">
              <span class="fonte-badge openalex">OpenAlex</span>
              ${window.config?.SCOPUS_API_KEY ? '<span class="fonte-badge scopus">Scopus</span>' : ''}
              ${window.config?.WOS_API_KEY ? '<span class="fonte-badge wos">WoS</span>' : ''}
            </div>
          </div>
        </div>

        <div class="bases-linhas">
          ${linhas.map(linha => BasesUI.montarCartaLinha(linha)).join('')}
        </div>
      </div>
    `;
  },

  /**
   * Monta card individual de linha de pesquisa com métricas
   */
  montarCartaLinha(linha) {
    const taxa = ((linha.artigos_com_dados / linha.total_artigos) * 100).toFixed(0);
    const cor = linha.media_citacoes > 5 ? 'success' : linha.media_citacoes > 2 ? 'warning' : 'info';

    return `
      <div class="linha-card ${cor}">
        <div class="linha-header">
          <h3>${linha.nome}</h3>
          <span class="linha-cobertura">${taxa}% coverage</span>
        </div>

        <div class="linha-metricas">
          <div class="metrica-pequena">
            <span class="label">Articles</span>
            <span class="valor">${linha.total_artigos}</span>
          </div>
          <div class="metrica-pequena">
            <span class="label">Citations</span>
            <span class="valor">${linha.total_citacoes}</span>
          </div>
          <div class="metrica-pequena">
            <span class="label">Avg</span>
            <span class="valor">${linha.media_citacoes.toFixed(1)}</span>
          </div>
        </div>

        <div class="linha-progresso">
          <div class="progresso-bar">
            <div class="progresso-fill" style="width: ${taxa}%"></div>
          </div>
        </div>
      </div>
    `;
  },

  /**
   * Monta tabela de top artigos mais citados
   */
  montarTopArtigos(dados, limite = 5) {
    if (!dados?.linhas) return '';

    // Coletar todos os artigos e ordenar por citações
    const artigos = [];
    for (const linha of dados.linhas) {
      for (const art of (linha.artigos || [])) {
        artigos.push({
          ...art,
          linha: linha.nome,
        });
      }
    }

    const topArtigos = artigos
      .sort((a, b) => (b.citacoes || 0) - (a.citacoes || 0))
      .slice(0, limite);

    return `
      <div class="top-artigos">
        <h3>
          <i data-lucide="award"></i>
          Most Cited
        </h3>
        <div class="artigos-lista">
          ${topArtigos.map((art, idx) => `
            <div class="artigo-item rank-${idx + 1}">
              <span class="rank">#${idx + 1}</span>
              <div class="artigo-info">
                <div class="artigo-titulo">${art.titulo || 'Untitled'}</div>
                <div class="artigo-meta">
                  <span>${art.linha}</span>
                  ${art.revista ? `<span>${art.revista}</span>` : ''}
                  <span>${art.ano_publicacao || '—'}</span>
                </div>
              </div>
              <div class="artigo-citacoes">${art.citacoes || 0}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  },

  /**
   * Monta miniatura de status das APIs
   */
  montarStatusApis() {
    return `
      <div class="apis-status">
        <h4>API Status</h4>
        <div class="status-list">
          <div class="status-item">
            <span class="status-dot ok"></span>
            <span>OpenAlex (live)</span>
          </div>
          <div class="status-item ${window.config?.SCOPUS_API_KEY ? 'ok' : 'disabled'}">
            <span class="status-dot"></span>
            <span>Scopus</span>
          </div>
          <div class="status-item ${window.config?.WOS_API_KEY ? 'ok' : 'disabled'}">
            <span class="status-dot"></span>
            <span>Web of Science</span>
          </div>
        </div>
      </div>
    `;
  },

  /**
   * Gráfico de evolução de citações ao longo do tempo
   */
  montarGraficoCitacoes(dados) {
    if (!dados?.linhas || dados.linhas.length === 0) return '';

    const linhas = dados.linhas.slice(0, 5); // Top 5 linhas
    const alturaMax = 300;
    const largura = 400;

    // Simulação: usar ordem das linhas como "tempo"
    const maxCitacoes = Math.max(...linhas.map(l => l.media_citacoes || 0), 1);

    return `
      <div class="grafico-citacoes">
        <h3>Citation Trend (by Research Line)</h3>
        <svg width="${largura}" height="${alturaMax}" class="chart">
          <defs>
            <linearGradient id="gradCitacoes" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#22c55e;stop-opacity:0.6" />
              <stop offset="100%" style="stop-color:#22c55e;stop-opacity:0" />
            </linearGradient>
          </defs>

          <!-- Grid -->
          ${[1, 2, 3, 4, 5].map(i => {
            const y = (alturaMax * i) / 5;
            return `<line x1="0" y1="${y}" x2="${largura}" y2="${y}" stroke="#333" stroke-dasharray="2,2" opacity="0.3"/>`;
          }).join('')}

          <!-- Barras de citações -->
          ${linhas.map((linha, idx) => {
            const altura = (linha.media_citacoes / maxCitacoes) * (alturaMax - 30);
            const x = (largura / linhas.length) * idx + 20;
            const y = alturaMax - altura - 20;
            const cor = linha.media_citacoes > 5 ? '#22c55e' : linha.media_citacoes > 2 ? '#f59e0b' : '#3b82f6';
            return `
              <g class="barra-grupo">
                <rect x="${x}" y="${y}" width="30" height="${altura}" fill="${cor}" rx="3" opacity="0.8"/>
                <text x="${x + 15}" y="${alturaMax - 5}" text-anchor="middle" font-size="10" fill="#999">
                  ${Math.round(linha.media_citacoes * 10) / 10}
                </text>
              </g>
            `;
          }).join('')}
        </svg>
      </div>
    `;
  },
};

/**
 * Integra componentes de bases no painel Ao Vivo
 */
function renderizarSecaoCitacoes(container) {
  if (!window.dados?.citacoes) return;

  const secao = document.createElement('section');
  secao.id = 'bases-dados';
  secao.className = 'secao-bases';
  secao.innerHTML = `
    <div class="bases-wrapper">
      ${BasesUI.montarPainelCitacoes(window.dados.citacoes)}
      <div class="bases-grid">
        ${BasesUI.montarTopArtigos(window.dados.citacoes)}
        ${BasesUI.montarGraficoCitacoes(window.dados.citacoes)}
      </div>
      ${BasesUI.montarStatusApis()}
    </div>
  `;

  container.appendChild(secao);

  // Inicializar ícones Lucide
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Exportar para uso em templates
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BasesUI;
}
