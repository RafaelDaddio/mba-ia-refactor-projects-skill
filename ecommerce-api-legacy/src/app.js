const express = require('express');
const { loadConfig } = require('./config');
const { Database } = require('./database/connection');
const { initSchema, seedIfEmpty } = require('./database/schema');
const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { ReportModel } = require('./models/reportModel');
const { CheckoutService } = require('./services/checkoutService');
const { ReportService } = require('./services/reportService');
const { UserService } = require('./services/userService');
const { buildCheckoutController } = require('./controllers/checkoutController');
const { buildReportController } = require('./controllers/reportController');
const { buildUserController } = require('./controllers/userController');
const { buildCheckoutRoutes } = require('./routes/checkoutRoutes');
const { buildReportRoutes } = require('./routes/reportRoutes');
const { buildUserRoutes } = require('./routes/userRoutes');
const { adminAuth } = require('./middlewares/adminAuth');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const { logger } = require('./utils/logger');

// Composition root: monta models, services, controllers e rotas com as dependências injetadas.
function createApp({ db, config }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json());

  const runInTransaction = (work) => db.transaction(work);
  const users = new UserModel(db);
  const courses = new CourseModel(db);
  const enrollments = new EnrollmentModel(db);
  const payments = new PaymentModel(db);
  const auditLogs = new AuditLogModel(db);
  const reports = new ReportModel(db);

  const checkoutService = new CheckoutService({
    runInTransaction, users, courses, enrollments, payments, auditLogs, logger,
  });
  const reportService = new ReportService({ reports });
  const userService = new UserService({ runInTransaction, users, enrollments, payments });

  app.use('/api', buildCheckoutRoutes({ checkoutController: buildCheckoutController({ checkoutService }) }));
  app.use('/api', buildReportRoutes({
    reportController: buildReportController({ reportService }),
    adminAuth: adminAuth(config.adminToken),
  }));
  app.use('/api', buildUserRoutes({ userController: buildUserController({ userService }) }));

  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}

async function main() {
  const config = loadConfig();
  const db = await Database.open(config.databasePath);
  await initSchema(db);
  if (config.seedOnStart && (await seedIfEmpty(db))) {
    logger.info('Banco populado com os dados de exemplo');
  }
  if (!config.adminToken) {
    logger.warn('ADMIN_TOKEN não definido: as rotas /api/admin/* vão responder 401');
  }

  const server = createApp({ db, config }).listen(config.port, config.host, () => {
    logger.info(`LMS API rodando em http://${config.host}:${config.port}`);
  });
  server.on('error', (err) => {
    logger.error('Falha ao abrir a porta', { error: err.message });
    process.exit(1);
  });
}

if (require.main === module) {
  main().catch((err) => {
    logger.error('Falha ao iniciar a aplicação', { error: err.stack });
    process.exit(1);
  });
}

module.exports = { createApp };
