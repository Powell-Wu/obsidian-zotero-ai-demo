---
type: literature-note
citekey: tunnermann2026DataModel
doi: 10.1103/kk2s-s43l
year: 2026
stage: ai-before
reading_level: full-text-source-available
source_item: DEMO001
privacy: new-demo-annotations-only
---

# AI 整理前｜批注导入（尚未结构化）

> [!warning] 阶段标记：AI BEFORE
> 本页模拟把新建的 Zotero 高亮与评论原样放在一起。保留页码和 citekey，但尚未建立证据等级、统一术语或组会逻辑。`Demo Reader` 是虚构读者；其评论不是论文证据。

## 条目（从新建题录复制）

**Data-model-guided framework for systemic emittance minimization in high-brightness photoinjectors**  
H. Tünnermann et al. · 2026 · Physical Review Accelerators and Beams 29(5), 050701  
DOI：https://doi.org/10.1103/kk2s-s43l  
citekey：`tunnermann2026DataModel`  
附件：[[99附件/tunnermann2026-data-model-guided-emittance.pdf|公开 PDF]]

## 高亮 + 评论（未整理）

### DEMO-A04 / p7 / 绿色

> A pulse energy of about 1.7 mJ has been achieved for SASE 1 at 7.1 keV photon energy and for SASE 2 at about 7.6 keV photon energy.

- 结果挺好，组会可以讲。
- 两条线站都是 1.7 mJ。
- 别忘了有限 tuning time（在哪里？同页上一段）。

### DEMO-A01 / p1 / 黄色

> A measured central slice emittance of about 0.4 μm at 250 pC is achieved using a 20 ps flattop laser pulse at the photocathode.

- 0.4 μm / 250 pC / 20 ps。
- 中央 slice，不是 projected。

### DEMO-A03 / p6 / 绿色

> At 200 pC, the optimized projected emittance is about 0.36 μm, with mismatch values of 1.6 in x and 1.1 in y.

- 这里又有 0.36！和上面的 0.4 不要混。
- 下一段说 Gaussian 是 0.46，所以约 20%。
- TODO：把“约 20%”的完整原文补到结构化笔记，不只凭评论记数字。

### DEMO-A02 / p5 / 蓝色

> To be precise, the modeling with extended measurements yielded (i) a faster training convergence, (ii) a decreased test prediction error by around one order of magnitude, (iii) a reduction of model complexity by approximately 50% (measured by the number of parameters) while maintaining the same prediction accuracy compared to the model with measurements y as defined in (1).

- 加了 slice misalignment ζ 后更好。
- “one order”是 prediction error，不是 emittance！
- 仿真，30,000 组？回 p3 核对。

### DEMO-A05 / p5 / 橙色

> the spatial shaping of the laser pulses, which can potentially further improve the bunch emittance, is not considered in this paper

- 范围：没做 spatial shaping。

### DEMO-A06 / p8 / 橙色

> The data that support the findings of this article are not publicly available. The data are available from the authors upon reasonable request.

- OA 论文 ≠ 开放数据。
- 展示时不能暗示拿到了原始数据。

## 随手问题（尚未回答）

- 框架的两个 model 分别做什么？#待整理
- 20 ps 和 0.4 μm 是摘要结果，20% 是另一个条件下的比较，怎么讲清楚？
- “ longer lasing window ”似乎只是 evidence suggested，不能写“显著提升稳定性”。
- 物理模型闭环和端到端全自动优化是不是一回事？可能不是。
- 组会主线：激光形状 → 束流分布 → 发射度 → FEL commissioning。

## 待 AI 第一遍处理

- [ ] 补全元数据和来源许可。
- [ ] 把高亮按“方法 / 仿真 / 实验 / FEL / 限制”分类。
- [ ] 每条事实附 PDF 页码和 ER 编号。
- [ ] 区分原文、读者评论和演示解读。
- [ ] 不把 0.36、0.4、0.46 μm 合并成同一测量。
- [ ] 不把仿真预测误差与实验发射度改善混为一谈。

**下一页**：[[01文献笔记/tunnermann2026-AI第一遍-证据笔记|AI 第一遍：证据笔记]]
