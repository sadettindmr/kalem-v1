"""add_search_vector_fts

Revision ID: f13a1c9d0b77
Revises: ea63d692364c, 8e16fefc38a1
Create Date: 2026-02-15 22:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f13a1c9d0b77"
down_revision: Union[str, Sequence[str], None] = ("ea63d692364c", "8e16fefc38a1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("papers", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))
    op.create_index(
        "ix_papers_search_vector",
        "papers",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )

    # papers satiri icin title + abstract + authors adlariyla search_vector hesapla
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_papers_search_vector(p_id integer)
        RETURNS void AS $$
        BEGIN
            UPDATE papers p
            SET search_vector =
                setweight(to_tsvector('english', coalesce(p.title, '')), 'A')
                ||
                setweight(to_tsvector('english', coalesce(p.abstract, '')), 'B')
                ||
                setweight(
                    to_tsvector(
                        'english',
                        coalesce(
                            (
                                SELECT string_agg(a.name, ' ')
                                FROM paper_authors pa
                                JOIN authors a ON a.id = pa.author_id
                                WHERE pa.paper_id = p.id
                            ),
                            ''
                        )
                    ),
                    'C'
                )
            WHERE p.id = p_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # papers insert/update icin trigger
    op.execute(
        """
        CREATE OR REPLACE FUNCTION papers_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A')
                ||
                setweight(to_tsvector('english', coalesce(NEW.abstract, '')), 'B')
                ||
                setweight(
                    to_tsvector(
                        'english',
                        coalesce(
                            (
                                SELECT string_agg(a.name, ' ')
                                FROM paper_authors pa
                                JOIN authors a ON a.id = pa.author_id
                                WHERE pa.paper_id = NEW.id
                            ),
                            ''
                        )
                    ),
                    'C'
                );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_papers_search_vector
        BEFORE INSERT OR UPDATE OF title, abstract ON papers
        FOR EACH ROW
        EXECUTE FUNCTION papers_search_vector_trigger();
        """
    )

    # author-paper iliskisi degisince ilgili paper'larin vectorunu yenile
    op.execute(
        """
        CREATE OR REPLACE FUNCTION paper_authors_search_vector_trigger()
        RETURNS trigger AS $$
        DECLARE
            target_paper_id integer;
        BEGIN
            target_paper_id := COALESCE(NEW.paper_id, OLD.paper_id);
            PERFORM update_papers_search_vector(target_paper_id);
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_paper_authors_search_vector
        AFTER INSERT OR UPDATE OR DELETE ON paper_authors
        FOR EACH ROW
        EXECUTE FUNCTION paper_authors_search_vector_trigger();
        """
    )

    # author adi degisirse bagli paper'larin vectorunu yenile
    op.execute(
        """
        CREATE OR REPLACE FUNCTION authors_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            UPDATE papers p
            SET search_vector =
                setweight(to_tsvector('english', coalesce(p.title, '')), 'A')
                ||
                setweight(to_tsvector('english', coalesce(p.abstract, '')), 'B')
                ||
                setweight(
                    to_tsvector(
                        'english',
                        coalesce(
                            (
                                SELECT string_agg(a.name, ' ')
                                FROM paper_authors pa
                                JOIN authors a ON a.id = pa.author_id
                                WHERE pa.paper_id = p.id
                            ),
                            ''
                        )
                    ),
                    'C'
                )
            WHERE p.id IN (
                SELECT pa.paper_id
                FROM paper_authors pa
                WHERE pa.author_id = NEW.id
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_authors_search_vector
        AFTER UPDATE OF name ON authors
        FOR EACH ROW
        EXECUTE FUNCTION authors_search_vector_trigger();
        """
    )

    # mevcut veriler icin backfill
    op.execute("UPDATE papers SET search_vector = NULL;")
    op.execute(
        """
        UPDATE papers p
        SET search_vector =
            setweight(to_tsvector('english', coalesce(p.title, '')), 'A')
            ||
            setweight(to_tsvector('english', coalesce(p.abstract, '')), 'B')
            ||
            setweight(
                to_tsvector(
                    'english',
                    coalesce(
                        (
                            SELECT string_agg(a.name, ' ')
                            FROM paper_authors pa
                            JOIN authors a ON a.id = pa.author_id
                            WHERE pa.paper_id = p.id
                        ),
                        ''
                    )
                ),
                'C'
            );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trg_authors_search_vector ON authors;")
    op.execute("DROP FUNCTION IF EXISTS authors_search_vector_trigger();")

    op.execute("DROP TRIGGER IF EXISTS trg_paper_authors_search_vector ON paper_authors;")
    op.execute("DROP FUNCTION IF EXISTS paper_authors_search_vector_trigger();")

    op.execute("DROP TRIGGER IF EXISTS trg_papers_search_vector ON papers;")
    op.execute("DROP FUNCTION IF EXISTS papers_search_vector_trigger();")

    op.execute("DROP FUNCTION IF EXISTS update_papers_search_vector(integer);")

    op.drop_index("ix_papers_search_vector", table_name="papers")
    op.drop_column("papers", "search_vector")
