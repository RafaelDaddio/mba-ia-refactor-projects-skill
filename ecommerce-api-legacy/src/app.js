const express = require('express');

const { loadConfig } = require('./config');
const { Database } = require('./database/connection');
const { initSchema } = require('./database/schema');
const { seedIfEmpty } = require('./database/seed');
const { buildCheckoutController } = require('./controllers/checkoutController');
const { buildReportController } = require('./controllers/reportController');
const { buildUserController } = require('./controllers/userController');
const { buildAuth } = require('./middlewares/auth');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const { AuditLogModel } = require('./models/auditLogModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { ReportModel } = require('./models/reportModel');
const { UserModel } = require('./models/userModel');
const { buildCheckoutRoutes } = require('./routes/checkoutRoutes');
const { buildReportRoutes } = require('./routes/reportRoutes');
const { buildUserRoutes } = require('./routes/userRoutes');
const { CheckoutService } = require('./services/checkoutService');
const { PaymentService } = require('./services/paymentService');
const { ReportService } = require('./services/reportService');
const { UserService } = require('./services/userService');
const { logger } = require('./utils/logger');

const API_PREFIX = '/api';

/** Composition root: monta a aplicação com o banco e a configuração recebidos. */
function createApp({ db, config }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json());

  const transaction = (work) => db.transaction(work);
  const users = new UserModel(db);
  const courses = new CourseModel(db);
  const enrollments = new EnrollmentModel(db);
  const payments = new PaymentModel(db);
  const auditLogs = new AuditLogModel(db);
  const reports = new ReportModel(db);

  const paymentService = new PaymentService({ gatewayKey: config.paymentGatewayKey, logger });
  const checkoutService = new CheckoutService({
    users,
    courses,
    enrollments,
    payments,
    auditLogs,
    paymentService,
    transaction,
    logger,
  });
  const reportService = new ReportService({ reports });
  const userService = new UserService({ users, enrollments, payments, transaction });

  const auth = buildAuth(config);
  app.use(API_PREFIX, buildCheckoutRoutes({ checkoutController: buildCheckoutController({ checkoutService }), auth }));
  app.use(API_PREFIX, buildReportRoutes({ reportController: buildReportController({ reportService }), auth }));
  app.use(API_PREFIX, buildUserRoutes({ userController: buildUserController({ userService }), auth }));

  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}

function warnAboutMissingSecrets(config) {
  if (!config.adminToken) {
    logger.warn('ADMIN_TOKEN não definido: o relatório financeiro e a exclusão de usuários respondem 401.');
  }
  if (!config.paymentGatewayKey) {
    logger.warn('PAYMENT_GATEWAY_KEY não definida: integração com o gateway desabilitada; a aprovação segue a regra simulada.');
  }
}

async function main() {
  const config = loadConfig();
  warnAboutMissingSecrets(config);

  const db = await Database.open(config.databasePath);
  await initSchema(db);
  if (config.seedOnStart && (await seedIfEmpty(db))) logger.info('Dados de exemplo carregados');

  const app = createApp({ db, config });
  await new Promise((resolve, reject) => {
    app.listen(config.port, config.host, resolve).on('error', reject);
  });
  logger.info(`Frankenstein LMS rodando em http://${config.host}:${config.port}`);
}

if (require.main === module) {
  main().catch((err) => {
    logger.error('Falha ao iniciar', { error: err.stack });
    process.exit(1);
  });
}

module.exports = { createApp };
