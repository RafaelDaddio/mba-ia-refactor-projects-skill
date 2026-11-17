function buildReportController({ reportService }) {
  return {
    async financial(req, res) {
      res.status(200).json(await reportService.financialReport());
    },
  };
}

module.exports = { buildReportController };
