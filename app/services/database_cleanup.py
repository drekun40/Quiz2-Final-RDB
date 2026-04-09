"""
Database cleanup utilities for removing duplicate player records
"""
from sqlmodel import Session, select, delete
from app.models import Player, Team
from app.database import get_engine, AVAILABLE_SEASONS
from app.services.deduplication import DeduplicationService
from typing import Tuple


class DatabaseCleanup:
    """Utilities for cleaning up duplicate player records in season databases"""
    
    @staticmethod
    def delete_duplicate_players(session: Session) -> Tuple[int, int, int]:
        """
        Delete duplicate player records, keeping only the lowest ID for each name.
        
        IMPORTANT: This operation is destructive and should be used carefully.
        Always run find_duplicate_players() first to see what will be deleted.
        
        Args:
            session: SQLAlchemy session for the database
        
        Returns:
            Tuple of (deleted_count, remaining_count, duplicate_count_before)
        """
        # Get duplicate count before deletion
        total_before, unique_before, dup_count_before = DeduplicationService.count_duplicates(session)
        
        # Get IDs to delete
        ids_to_delete = DeduplicationService.get_duplicate_ids_to_delete(session)
        
        # Delete these players
        if ids_to_delete:
            stmt = delete(Player).where(Player.id.in_(ids_to_delete))
            result = session.exec(stmt)
            session.commit()
            deleted_count = len(ids_to_delete)
        else:
            deleted_count = 0
        
        # Get new count
        total_after, unique_after, dup_count_after = DeduplicationService.count_duplicates(session)
        
        return (deleted_count, total_after, dup_count_before)
    
    @staticmethod
    def cleanup_season(season: int, dry_run: bool = True) -> dict:
        """
        Clean up a single season database.
        
        Args:
            season: The season year to clean
            dry_run: If True, only count duplicates without deleting
        
        Returns:
            Dict with cleanup statistics
                {
                    'season': 2019,
                    'before': {'total': 33, 'unique': 23, 'duplicates': 10},
                    'after': {'total': 23, 'unique': 23, 'duplicates': 0},
                    'deleted': 10,
                    'dry_run': True
                }
        """
        engine = get_engine(season)
        session = Session(engine)
        
        try:
            # Get before stats
            total_before, unique_before, dup_before = DeduplicationService.count_duplicates(session)
            
            if dry_run:
                # Don't actually delete
                ids_to_delete = DeduplicationService.get_duplicate_ids_to_delete(session)
                deleted_count = len(ids_to_delete)
                total_after = total_before - deleted_count
                unique_after = unique_before
                dup_after = 0
            else:
                # Actually delete
                deleted_count, total_after, _ = DatabaseCleanup.delete_duplicate_players(session)
                _, unique_after, dup_after = DeduplicationService.count_duplicates(session)
            
            return {
                'season': season,
                'before': {
                    'total': total_before,
                    'unique': unique_before,
                    'duplicates': dup_before
                },
                'after': {
                    'total': total_after,
                    'unique': unique_after,
                    'duplicates': dup_after
                },
                'deleted': deleted_count,
                'dry_run': dry_run,
                'status': 'success'
            }
        
        except Exception as e:
            return {
                'season': season,
                'status': 'error',
                'error': str(e),
                'dry_run': dry_run
            }
        
        finally:
            session.close()
    
    @staticmethod
    def cleanup_all_seasons(dry_run: bool = True) -> dict:
        """
        Clean up all season databases.
        
        Args:
            dry_run: If True, only count what would be deleted
        
        Returns:
            Dict with cleanup statistics for all seasons
                {
                    'all_seasons': [
                        {'season': 2010, 'before': {...}, 'after': {...}, 'deleted': X},
                        ...
                    ],
                    'total_deleted': 150,
                    'dry_run': True
                }
        """
        results = []
        total_deleted = 0
        
        for season in AVAILABLE_SEASONS:
            result = DatabaseCleanup.cleanup_season(season, dry_run=dry_run)
            results.append(result)
            if result['status'] == 'success':
                total_deleted += result['deleted']
        
        return {
            'all_seasons': results,
            'total_deleted': total_deleted,
            'dry_run': dry_run,
            'seasons_processed': len(AVAILABLE_SEASONS)
        }
    
    @staticmethod
    def verify_data_integrity_season(session: Session) -> dict:
        """
        Verify data integrity of a season database.
        
        Returns:
            Dict with verification results
        """
        results = {
            'duplicates_found': False,
            'issues': [],
            'stats': {}
        }
        
        # Check for duplicate player names
        duplicates = DeduplicationService.find_duplicate_players(session)
        
        if duplicates:
            results['duplicates_found'] = True
            results['issues'].append(f"Found {len(duplicates)} player names that appear multiple times")
            
            for player_name, ids in duplicates.items():
                results['issues'].append(f"  - {player_name}: {len(ids)} records (IDs: {ids})")
                
                # Check if stats are identical
                if DeduplicationService.validate_duplicate_stats_are_identical(session, player_name):
                    results['issues'].append(f"    → Stats are identical (safe to clean up)")
                else:
                    results['issues'].append(f"    → Stats differ! (MANUAL REVIEW NEEDED)")
        
        # Get stats
        total, unique, dup = DeduplicationService.count_duplicates(session)
        results['stats'] = {
            'total_players': total,
            'unique_players': unique,
            'duplicate_records': dup
        }
        
        return results
    
    @staticmethod
    def print_cleanup_report(cleanup_result: dict):
        """
        Pretty print a cleanup result dictionary.
        
        Args:
            cleanup_result: Result from cleanup_season() or cleanup_all_seasons()
        """
        if 'all_seasons' in cleanup_result:
            # All seasons cleanup
            print("\n" + "="*70)
            print("🧹 DATABASE CLEANUP REPORT - ALL SEASONS")
            print("="*70)
            print(f"Dry Run: {cleanup_result['dry_run']}")
            print(f"Seasons: {cleanup_result['seasons_processed']}")
            print(f"Total to Delete: {cleanup_result['total_deleted']}")
            print()
            
            for result in cleanup_result['all_seasons']:
                if result['status'] == 'success':
                    print(f"Season {result['season']}:")
                    print(f"  Before: {result['before']['total']} total, {result['before']['unique']} unique, {result['before']['duplicates']} dups")
                    print(f"  After:  {result['after']['total']} total, {result['after']['unique']} unique, {result['after']['duplicates']} dups")
                    print(f"  Deleted: {result['deleted']}")
                else:
                    print(f"Season {result['season']}: ERROR - {result['error']}")
        else:
            # Single season cleanup
            print("\n" + "="*70)
            print(f"🧹 DATABASE CLEANUP REPORT - SEASON {cleanup_result['season']}")
            print("="*70)
            print(f"Dry Run: {cleanup_result['dry_run']}")
            print()
            
            if cleanup_result['status'] == 'success':
                print(f"Before:")
                print(f"  Total: {cleanup_result['before']['total']}")
                print(f"  Unique: {cleanup_result['before']['unique']}")
                print(f"  Duplicates: {cleanup_result['before']['duplicates']}")
                print()
                print(f"After:")
                print(f"  Total: {cleanup_result['after']['total']}")
                print(f"  Unique: {cleanup_result['after']['unique']}")
                print(f"  Duplicates: {cleanup_result['after']['duplicates']}")
                print()
                print(f"Deleted: {cleanup_result['deleted']}")
            else:
                print(f"ERROR: {cleanup_result['error']}")
        
        print("="*70 + "\n")
