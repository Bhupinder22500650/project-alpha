"""Initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create domains table
    op.create_table('domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_name', sa.String(), nullable=False),
        sa.Column('registered_domain', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('received', 'normalised', 'initially_scored', 'enrichment_pending', 'enriching', 'fully_scored', 'enrichment_failed', 'reviewed', 'closed', name='processingstate'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_domains_domain_name'), 'domains', ['domain_name'], unique=True)
    op.create_index(op.f('ix_domains_id'), 'domains', ['id'], unique=False)
    op.create_index(op.f('ix_domains_registered_domain'), 'domains', ['registered_domain'], unique=False)

    # 2. Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'analyst', name='userrole'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 3. Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('new', 'under_review', 'confirmed_suspicious', 'false_positive', 'closed', name='alertstatus'), nullable=True),
        sa.Column('analyst_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['analyst_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_domain_id'), 'alerts', ['domain_id'], unique=False)
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)

    # 4. Create domain_enrichments table
    op.create_table('domain_enrichments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('rdap_registration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rdap_expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rdap_registrar', sa.String(), nullable=True),
        sa.Column('rdap_domain_age_days', sa.Integer(), nullable=True),
        sa.Column('dns_a_record_count', sa.Integer(), nullable=True),
        sa.Column('dns_mx_record_present', sa.Boolean(), nullable=True),
        sa.Column('dns_ns_record_count', sa.Integer(), nullable=True),
        sa.Column('cert_issuer', sa.String(), nullable=True),
        sa.Column('cert_validity_days', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_domain_enrichments_domain_id'), 'domain_enrichments', ['domain_id'], unique=False)
    op.create_index(op.f('ix_domain_enrichments_id'), 'domain_enrichments', ['id'], unique=False)

    # 5. Create features table
    op.create_table('features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('length', sa.Integer(), nullable=True),
        sa.Column('entropy', sa.Float(), nullable=True),
        sa.Column('digit_ratio', sa.Float(), nullable=True),
        sa.Column('hyphen_count', sa.Integer(), nullable=True),
        sa.Column('keyword_match', sa.Boolean(), nullable=True),
        sa.Column('levenshtein_min', sa.Integer(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_features_domain_id'), 'features', ['domain_id'], unique=False)
    op.create_index(op.f('ix_features_id'), 'features', ['id'], unique=False)

    # 6. Create scores table
    op.create_table('scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('fast_lexical_score', sa.Float(), nullable=True),
        sa.Column('final_risk_score', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('top_factors', sa.JSON(), nullable=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scores_domain_id'), 'scores', ['domain_id'], unique=False)
    op.create_index(op.f('ix_scores_id'), 'scores', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('scores')
    op.drop_table('features')
    op.drop_table('domain_enrichments')
    op.drop_table('alerts')
    op.drop_table('users')
    op.drop_table('domains')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS processingstate;")
    op.execute("DROP TYPE IF EXISTS userrole;")
    op.execute("DROP TYPE IF EXISTS alertstatus;")
