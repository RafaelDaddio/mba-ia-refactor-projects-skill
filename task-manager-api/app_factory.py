"""Composition root: cria a aplicação e injeta as dependências."""
from flask import Flask
from flask_cors import CORS

from controllers.auth_controller import AuthController
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db, init_db
from middlewares.auth import init_auth
from middlewares.error_handler import register_error_handlers
from models import CategoryRepository, TaskRepository, UserRepository
from routes import auth_routes, category_routes, report_routes, system_routes, task_routes, user_routes
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService
from utils.logger import configure_logging


def create_app(settings):
    configure_logging(settings.debug)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        ADMIN_TOKEN=settings.admin_token,
        SQLALCHEMY_DATABASE_URI=settings.database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    CORS(app, origins=settings.cors_origins)
    init_db(app)

    # models (acesso a dados) -> services (regras) -> controllers (HTTP)
    tasks = TaskRepository(db.session)
    users = UserRepository(db.session)
    categories = CategoryRepository(db.session)

    auth_service = AuthService(users)
    task_service = TaskService(tasks, users, categories)
    user_service = UserService(users, tasks)
    category_service = CategoryService(categories)
    report_service = ReportService(tasks, users, categories)

    init_auth(app, auth_service.load_account)
    register_error_handlers(app)

    app.register_blueprint(system_routes.create_blueprint())
    app.register_blueprint(auth_routes.create_blueprint(AuthController(auth_service)))
    app.register_blueprint(task_routes.create_blueprint(TaskController(task_service)))
    app.register_blueprint(user_routes.create_blueprint(UserController(user_service)))
    app.register_blueprint(category_routes.create_blueprint(CategoryController(category_service)))
    app.register_blueprint(report_routes.create_blueprint(ReportController(report_service)))

    return app
