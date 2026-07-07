"""initial migration

Revision ID: 0001
Revises: 
Create Date: 2026-07-07 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- ROLES ---
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_roles_name'), 'roles', ['name'], unique=True)

    # --- USERS ---
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('idx_users_role_id'), 'users', ['role_id'], unique=False)
    op.create_index(op.f('idx_users_created_at'), 'users', ['created_at'], unique=False)

    # --- EVENTS ---
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_events_timestamp'), 'events', ['timestamp'], unique=False)
    op.create_index(op.f('idx_events_type'), 'events', ['type'], unique=False)
    op.create_index(op.f('idx_events_source'), 'events', ['source'], unique=False)

    # --- INCIDENTS ---
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('reporter_id', sa.String(length=36), nullable=True),
        sa.Column('assignee_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_summary', sa.String(), nullable=True),
        sa.Column('ai_root_cause', sa.String(), nullable=True),
        sa.Column('ai_lessons_learned', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_incidents_status'), 'incidents', ['status'], unique=False)
    op.create_index(op.f('idx_incidents_priority'), 'incidents', ['priority'], unique=False)
    op.create_index(op.f('idx_incidents_sector'), 'incidents', ['sector'], unique=False)
    op.create_index(op.f('idx_incidents_reporter_id'), 'incidents', ['reporter_id'], unique=False)
    op.create_index(op.f('idx_incidents_assignee_id'), 'incidents', ['assignee_id'], unique=False)
    op.create_index(op.f('idx_incidents_created_at'), 'incidents', ['created_at'], unique=False)

    # --- PREDICTIONS ---
    op.create_table(
        'predictions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('reasoning', sa.String(), nullable=False),
        sa.Column('predicted_outcome', sa.String(), nullable=True),
        sa.Column('suggested_actions', sa.JSON(), nullable=False),
        sa.Column('target_sector', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_predictions_incident_id'), 'predictions', ['incident_id'], unique=False)
    op.create_index(op.f('idx_predictions_type'), 'predictions', ['type'], unique=False)
    op.create_index(op.f('idx_predictions_target_sector'), 'predictions', ['target_sector'], unique=False)
    op.create_index(op.f('idx_predictions_created_at'), 'predictions', ['created_at'], unique=False)

    # --- RECOMMENDATIONS ---
    op.create_table(
        'recommendations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('prediction_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_recommendations_prediction_id'), 'recommendations', ['prediction_id'], unique=False)
    op.create_index(op.f('idx_recommendations_status'), 'recommendations', ['status'], unique=False)
    op.create_index(op.f('idx_recommendations_created_at'), 'recommendations', ['created_at'], unique=False)

    # --- TASKS ---
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=False),
        sa.Column('volunteer_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('eta_minutes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('idx_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('idx_tasks_incident_id'), 'tasks', ['incident_id'], unique=False)
    op.create_index(op.f('idx_tasks_volunteer_id'), 'tasks', ['volunteer_id'], unique=False)
    op.create_index(op.f('idx_tasks_created_at'), 'tasks', ['created_at'], unique=False)

    # --- NOTIFICATIONS ---
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recipient_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)
    op.create_index(op.f('idx_notifications_read'), 'notifications', ['read'], unique=False)
    op.create_index(op.f('idx_notifications_priority'), 'notifications', ['priority'], unique=False)
    op.create_index(op.f('idx_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('idx_notifications_created_at'), 'notifications', ['created_at'], unique=False)

    # --- CROWD METRICS ---
    op.create_table(
        'crowd_metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('density', sa.Float(), nullable=False),
        sa.Column('velocity', sa.Float(), nullable=False),
        sa.Column('wait_time_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_crowd_metrics_timestamp'), 'crowd_metrics', ['timestamp'], unique=False)
    op.create_index(op.f('idx_crowd_metrics_sector'), 'crowd_metrics', ['sector'], unique=False)
    op.create_index(op.f('idx_crowd_metrics_created_at'), 'crowd_metrics', ['created_at'], unique=False)

    # --- TRANSPORT ---
    op.create_table(
        'transport',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('route_name', sa.String(length=100), nullable=False),
        sa.Column('vehicle_id', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_stop', sa.String(length=100), nullable=True),
        sa.Column('occupancy_percentage', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transport_timestamp'), 'transport', ['timestamp'], unique=False)
    op.create_index(op.f('idx_transport_route_name'), 'transport', ['route_name'], unique=False)
    op.create_index(op.f('idx_transport_vehicle_id'), 'transport', ['vehicle_id'], unique=False)
    op.create_index(op.f('idx_transport_status'), 'transport', ['status'], unique=False)
    op.create_index(op.f('idx_transport_created_at'), 'transport', ['created_at'], unique=False)

    # --- PARKING ---
    op.create_table(
        'parking',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lot_name', sa.String(length=100), nullable=False),
        sa.Column('total_spots', sa.Integer(), nullable=False),
        sa.Column('occupied_spots', sa.Integer(), nullable=False),
        sa.Column('occupancy_percentage', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_parking_timestamp'), 'parking', ['timestamp'], unique=False)
    op.create_index(op.f('idx_parking_lot_name'), 'parking', ['lot_name'], unique=False)
    op.create_index(op.f('idx_parking_status'), 'parking', ['status'], unique=False)
    op.create_index(op.f('idx_parking_created_at'), 'parking', ['created_at'], unique=False)

    # --- ENERGY ---
    op.create_table(
        'energy',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('grid_zone', sa.String(length=100), nullable=False),
        sa.Column('active_power_kw', sa.Float(), nullable=False),
        sa.Column('reactive_power_kvar', sa.Float(), nullable=False),
        sa.Column('voltage', sa.Float(), nullable=False),
        sa.Column('load_percentage', sa.Float(), nullable=False),
        sa.Column('carbon_offset_kg', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_energy_timestamp'), 'energy', ['timestamp'], unique=False)
    op.create_index(op.f('idx_energy_grid_zone'), 'energy', ['grid_zone'], unique=False)
    op.create_index(op.f('idx_energy_created_at'), 'energy', ['created_at'], unique=False)

    # --- CARBON ---
    op.create_table(
        'carbon',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('emission_source', sa.String(length=100), nullable=False),
        sa.Column('amount_kg', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_carbon_timestamp'), 'carbon', ['timestamp'], unique=False)
    op.create_index(op.f('idx_carbon_emission_source'), 'carbon', ['emission_source'], unique=False)
    op.create_index(op.f('idx_carbon_category'), 'carbon', ['category'], unique=False)
    op.create_index(op.f('idx_carbon_created_at'), 'carbon', ['created_at'], unique=False)

    # --- REPLAY LOGS ---
    op.create_table(
        'replay_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('replay_session_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_replay_logs_replay_session_id'), 'replay_logs', ['replay_session_id'], unique=False)
    op.create_index(op.f('idx_replay_logs_timestamp'), 'replay_logs', ['timestamp'], unique=False)
    op.create_index(op.f('idx_replay_logs_event_type'), 'replay_logs', ['event_type'], unique=False)
    op.create_index(op.f('idx_replay_logs_created_at'), 'replay_logs', ['created_at'], unique=False)

    # --- TELEMETRY ---
    op.create_table(
        'telemetry',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_telemetry_timestamp'), 'telemetry', ['timestamp'], unique=False)
    op.create_index(op.f('idx_telemetry_metric_name'), 'telemetry', ['metric_name'], unique=False)
    op.create_index(op.f('idx_telemetry_sector'), 'telemetry', ['sector'], unique=False)
    op.create_index(op.f('idx_telemetry_created_at'), 'telemetry', ['created_at'], unique=False)

    # --- DECISIONS ---
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('prediction_id', sa.String(length=36), nullable=True),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('expected_impact', sa.String(), nullable=False),
        sa.Column('responsible_team', sa.String(length=100), nullable=False),
        sa.Column('eta', sa.String(length=50), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_decisions_prediction_id'), 'decisions', ['prediction_id'], unique=False)
    op.create_index(op.f('idx_decisions_incident_id'), 'decisions', ['incident_id'], unique=False)
    op.create_index(op.f('idx_decisions_action_type'), 'decisions', ['action_type'], unique=False)
    op.create_index(op.f('idx_decisions_created_at'), 'decisions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('decisions')
    op.drop_table('telemetry')
    op.drop_table('replay_logs')
    op.drop_table('carbon')
    op.drop_table('energy')
    op.drop_table('parking')
    op.drop_table('transport')
    op.drop_table('crowd_metrics')
    op.drop_table('notifications')
    op.drop_table('tasks')
    op.drop_table('recommendations')
    op.drop_table('predictions')
    op.drop_table('incidents')
    op.drop_table('events')
    op.drop_table('users')
    op.drop_table('roles')
