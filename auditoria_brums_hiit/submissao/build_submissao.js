const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,Table,TableRow,TableCell,WidthType,BorderStyle,ShadingType,PageBreak}=require('docx');
const NAVY='122438',TEAL='0E8C86',MUT='5B6B82',F='Calibri',SERIF='Cambria';
const OUT='/home/user/mdlucca/auditoria_brums_hiit/submissao/';

function P(runs,o={}){return new Paragraph({alignment:AlignmentType.JUSTIFIED,spacing:{after:160,line:276},...o,children:(Array.isArray(runs)?runs:[runs]).map(r=>typeof r==='string'?new TextRun({text:r,font:F,size:22}):r)});}
function T(t,o={}){return new TextRun({text:t,font:F,size:22,...o});}
function B(t){return new TextRun({text:t,font:F,size:22,bold:true});}

/* ============ 1) CARTA DE APRESENTAÇÃO ============ */
(function(){
const k=[];
k.push(new Paragraph({spacing:{after:60},children:[new TextRun({text:'[Cidade], [dia] de [mês] de 2026',font:F,size:22})]}));
k.push(new Paragraph({spacing:{after:40},children:[new TextRun({text:'À Editoria da revista [Nome do Periódico]',font:F,size:22,bold:true})]}));
k.push(new Paragraph({spacing:{after:200},children:[new TextRun({text:'A/C Editor(a)-Chefe',font:F,size:22})]}));
k.push(P('Prezado(a) Editor(a),'));
k.push(P([T('Submetemos à apreciação de '),B('[Nome do Periódico]'),T(' o manuscrito intitulado '),new TextRun({text:'"Resposta do estado de humor a um microciclo de treinamento intervalado de alta intensidade (HIIT) em atletas de handebol de elite: um estudo observacional de medidas repetidas"',font:F,size:22,italics:true}),T(', para consideração como artigo original.')]));
k.push(P([T('O estudo acompanhou '),B('27 atletas de handebol de elite'),T(' ao longo de um microciclo de sete dias com três sessões de HIIT, monitorando o estado de humor pela '),B('Escala de Humor de Brunel (BRUMS)'),T(' e a carga interna por frequência cardíaca e percepção subjetiva de esforço. Diferentemente da maior parte da literatura de monitoramento, a análise tratou '),B('o atleta como unidade'),T(' — modelos de efeitos mistos com correção de pseudorreplicação e da taxa de falsa descoberta —, garantindo inferência estatística apropriada para dados aninhados de medidas repetidas.')]));
k.push(P([T('Os principais achados são: (1) a resposta aguda ao HIIT é '),B('seletiva e ancorada no eixo energia–fadiga'),T(' — a fadiga física é o marcador-sentinela (d'),new TextRun({text:'z',font:F,size:16,subScript:true}),T(' ≈ 1,0; único com AUC ≥ 0,70), com queda concomitante de vigor, enquanto o afeto negativo permanece estável (com evidência bayesiana de equivalência); (2) a resposta é '),B('fortemente individual'),T(' (coeficientes de correlação intraclasse de 0,4 a 0,7; R² condicional muito superior ao marginal); e (3) o humor é '),B('desacoplado da carga interna'),T(' — nem a frequência cardíaca, nem a PSE, nem o TRIMP predizem a resposta aguda —, indicando que o BRUMS mede uma dimensão complementar, e não redundante, aos marcadores fisiológicos.')]));
k.push(P([T('As conclusões são sustentadas por uma bateria analítica ampla e '),B('inteiramente reproduzível por código'),T(' (análise fatorial confirmatória, invariância de medida, teoria de resposta ao item, fatores de Bayes, curvas ROC, TRIMP de Banister, modelos preditivos com validação leave-one-athlete-out e verificações de robustez por permutação e transformação). Todas as figuras e tabelas são geradas a partir da coleta bruta por um pipeline automatizado, e os achados sobrevivem a testes paramétricos e não-paramétricos, à transformação logarítmica e à exclusão de casos influentes.')]));
k.push(P([T('Do ponto de vista aplicado, o trabalho oferece uma recomendação concreta de monitoramento: acompanhar a '),B('fadiga física'),T(' e o eixo vigor–fadiga por tendência individual, com o humor como camada complementar à carga fisiológica. Uma contribuição psicométrica adicional é a identificação de que o item de sonolência do BRUMS se comporta de forma oposta aos demais itens de fadiga no plano agudo (o exercício reduz a sonolência ao ativar), sugerindo tratá-lo à parte da subescala.')]));
k.push(P('Declaramos que: o manuscrito é original e não foi publicado nem está sob avaliação em outro periódico; todos os autores leram e aprovaram a versão submetida e concordam com a submissão; não há conflitos de interesse a declarar; e o estudo foi conduzido em conformidade com a Declaração de Helsinque, com aprovação do Comitê de Ética em Pesquisa [nº do parecer] e consentimento livre e esclarecido de todos os participantes. Os dados foram anonimizados e as bases identificáveis não são compartilhadas publicamente.'));
k.push(P('Sugerimos que o manuscrito se enquadra no escopo do periódico por unir monitoramento psicológico e fisiológico da carga em atletas de elite com rigor metodológico e reprodutibilidade. Agradecemos a atenção e permanecemos à disposição para os esclarecimentos que se fizerem necessários.'));
k.push(new Paragraph({spacing:{before:200,after:20},children:[T('Atenciosamente,')]}));
k.push(new Paragraph({spacing:{before:200,after:0},children:[new TextRun({text:'[Nome do autor correspondente]',font:F,size:22,bold:true})]}));
k.push(new Paragraph({spacing:{after:0},children:[new TextRun({text:'[Afiliação] · [e-mail] · [ORCID]',font:F,size:20,color:MUT})]}));
k.push(new Paragraph({spacing:{after:0},children:[new TextRun({text:'em nome de todos os coautores',font:F,size:20,italics:true,color:MUT})]}));

const doc=new Document({styles:{default:{document:{run:{font:F,size:22}}}},
 sections:[{properties:{page:{margin:{top:1440,bottom:1440,left:1440,right:1440}}},
 children:[
   new Paragraph({spacing:{after:40},children:[new TextRun({text:'CARTA DE APRESENTAÇÃO',font:SERIF,bold:true,color:NAVY,size:30})]}),
   new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:8,color:TEAL}},spacing:{after:220},children:[new TextRun({text:'',size:2})]}),
   ...k
 ]}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(OUT+'Carta_apresentacao_BRUMS_HIIT.docx',b);console.log('Carta:',b.length,'bytes');});
})();

/* ============ 2) CHECKLIST STROBE ============ */
(function(){
const border={style:BorderStyle.SINGLE,size:2,color:'D5DCE6'};
const borders={top:border,bottom:border,left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideHorizontal:border,insideVertical:{style:BorderStyle.NONE}};
function cell(txt,{w,head=false,bold=false}={}){return new TableCell({width:{size:w,type:WidthType.DXA},shading:head?{type:ShadingType.CLEAR,fill:NAVY}:undefined,margins:{top:50,bottom:50,left:90,right:90},
  children:(Array.isArray(txt)?txt:[txt]).map(t=>new Paragraph({children:[new TextRun({text:t,font:F,size:16,bold:head||bold,color:head?'FFFFFF':'1A1A1A'})]}))});}
function row(n,item,onde){return new TableRow({children:[cell(n,{w:700}),cell(item,{w:5200}),cell(onde,{w:3900})]});}
const head=new TableRow({tableHeader:true,children:[cell('Item',{w:700,head:true}),cell('Recomendação STROBE',{w:5200,head:true}),cell('Onde é atendido no pacote',{w:3900,head:true})]});
const R=[
 ['1','Título e resumo — desenho no título; resumo informativo e balanceado','Título indica "estudo observacional de medidas repetidas"; resumo estruturado no manuscrito (ARTIGO_AUDITADO.docx)'],
 ['2','Introdução — contexto/justificativa científica','Introdução + revisão de literatura (PubMed) no manuscrito'],
 ['3','Objetivos — hipóteses pré-especificadas','Seção "Objetivos revisados" do manuscrito'],
 ['4','Desenho do estudo','Longitudinal observacional, medidas repetidas; §1 do Documento completo e figura de desenho analítico'],
 ['5','Contexto — locais, datas, períodos','Microciclo de 7 dias (21–27/04/2024), clube de handebol de elite'],
 ['6','Participantes — critérios de elegibilidade e seleção','27 atletas; funil de coletas (37 grafias → 27 atletas; 1 coleta fora da janela excluída → 456 obs.)'],
 ['7','Variáveis — desfechos, exposições, preditores, confundidores','BRUMS (6 subescalas + PTH), fadiga/estado físico e mental; exposição = dia de HIIT; §2–3'],
 ['8','Fontes de dados / mensuração','BRUMS validado (Rohlfs et al.); FC por frequencímetro; PSE (Foster); confiabilidade e invariância verificadas'],
 ['9','Viés — tratamento de fontes de viés','Correção de pseudorreplicação (atleta como unidade); anonimização; auditoria célula a célula'],
 ['10','Tamanho do estudo','27 atletas, 456 observações, 135 pares pré→pós; limitação de n discutida'],
 ['11','Variáveis quantitativas — categorização/manuseio','Escores contínuos; efeito piso reportado; transformação log como análise de sensibilidade'],
 ['12','Métodos estatísticos — modelos, subgrupos, dados faltantes, sensibilidade','Modelos mistos + FDR; MANOVA/PERMANOVA; Bayes; ROC; leave-one-athlete-out; permutação, log e exclusão de outlier (§ modelagem/, modelo_teorico/, perfil_variabilidade/)'],
 ['13','Participantes — números em cada etapa','Funil descrito; n por dia e por momento nos módulos'],
 ['14','Dados descritivos — características, dados faltantes','descritivas_testes/ (M, DP, mediana, IQR, assimetria, % piso, normalidade)'],
 ['15','Dados de desfecho — eventos/medidas resumo','Tabelas de resposta aguda e acúmulo (modelagem/, estatistica_inferencial/)'],
 ['16','Resultados principais — estimativas, IC, ajustes','β ± erro-padrão e IC95%; dz com IC bootstrap; R² marginal/condicional; ICC (modelo_teorico/)'],
 ['17','Outras análises — subgrupos, interações, sensibilidade','Segmentação (tipologia), interação Condição×Momento, comparação entre dias (dias_hiit/), robustez (perfil_variabilidade/)'],
 ['18','Resultados-chave — em relação aos objetivos','Síntese das três conclusões-âncora (Resultados e Discussão; Síntese dos achados)'],
 ['19','Limitações — viés e imprecisão','n pequeno; ausência de duração de sessão (TRIMP relativo); sem escala dedicada de sono; discutidas no manuscrito'],
 ['20','Interpretação — cautelosa e à luz da evidência','Discussão integrada; convergência de métodos; eixo energia–fadiga e individualidade'],
 ['21','Generalização — validade externa','Atletas de handebol de elite; escopo e transferência discutidos'],
 ['22','Financiamento — papel dos financiadores','[A preencher: fonte de financiamento / declaração de ausência]'],
];
const tbl=new Table({width:{size:9800,type:WidthType.DXA},columnWidths:[700,5200,3900],borders,rows:[head,...R.map(r=>row(r[0],r[1],r[2]))]});
const doc=new Document({styles:{default:{document:{run:{font:F,size:22}}}},
 sections:[{properties:{page:{margin:{top:1200,bottom:1200,left:1000,right:1000}}},children:[
  new Paragraph({spacing:{after:40},children:[new TextRun({text:'Checklist STROBE — estudos observacionais',font:SERIF,bold:true,color:NAVY,size:28})]}),
  new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:8,color:TEAL}},spacing:{after:160},children:[new TextRun({text:'',size:2})]}),
  new Paragraph({alignment:AlignmentType.JUSTIFIED,spacing:{after:200},children:[new TextRun({text:'Mapeamento dos 22 itens da diretriz STROBE (STrengthening the Reporting of OBservational studies in Epidemiology) ao local em que cada item é atendido no pacote analítico BRUMS × HIIT. Itens entre colchetes dependem de informações administrativas do estudo a serem preenchidas pelo autor.',font:F,size:19,italics:true,color:MUT})]}),
  tbl,
  new Paragraph({spacing:{before:200},children:[new TextRun({text:'Referência: von Elm E, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. Lancet, 2007.',font:F,size:16,italics:true,color:MUT})]}),
 ]}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync(OUT+'Checklist_STROBE_BRUMS_HIIT.docx',b);console.log('STROBE:',b.length,'bytes');});
})();
