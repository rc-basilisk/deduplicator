#!/usr/bin/env python3
"""
Command-line interface for File Deduplicator.

Usage:
    python cli.py scan /path/to/folder --types image document --threshold 0.95
    python cli.py list [session_id]
    python cli.py export <session_id> --output results.csv
"""
import argparse
import json
import sys
from datetime import datetime

from database import Database
from database.models import ScanSession, DuplicateGroup, FileEntry
from core import DuplicateScanner


def progress_callback(current, total, message):
    """Print progress to console"""
    bar_length = 40
    if total > 0:
        percent = current / total
        filled = int(bar_length * percent)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f'\r[{bar}] {percent*100:.1f}% - {message}', end='', flush=True)


def status_callback(message):
    """Print status message"""
    print(f'\n{message}')


def cmd_scan(args):
    """Run a duplicate scan"""
    db = Database()

    # Parse file types
    valid_types = ['image', 'document', 'video', 'archive', 'code']
    file_types = []
    for t in args.types:
        if t in valid_types:
            file_types.append(t)
        else:
            print(f"Warning: Unknown file type '{t}', skipping")

    if not file_types:
        print("Error: No valid file types specified")
        print(f"Valid types: {', '.join(valid_types)}")
        sys.exit(1)

    # Create scan session
    paths = args.paths if isinstance(args.paths, list) else [args.paths]
    session_name = f"CLI Scan {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session_id = db.create_scan_session(
        session_name,
        json.dumps(file_types),
        args.threshold
    )

    print(f"Starting scan session {session_id}")
    print(f"Paths: {', '.join(paths)}")
    print(f"File types: {', '.join(file_types)}")
    print(f"Similarity threshold: {args.threshold * 100}%")
    print()

    # Create scanner
    scanner = DuplicateScanner(
        db, session_id, file_types, args.threshold,
        thread_count=args.threads
    )

    # Run scan
    db.update_session_status(session_id, 'running')

    path_tuples = [(p, args.recursive) for p in paths]
    scanner.scan_paths(
        path_tuples,
        progress_callback=progress_callback,
        status_callback=status_callback
    )

    db.update_session_status(session_id, 'completed')

    # Print summary
    print("\n\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)

    session = db.get_session()
    try:
        groups = session.query(DuplicateGroup).filter_by(session_id=session_id).all()
        total_files = 0
        for group in groups:
            total_files += len(group.files)

        print(f"Session ID: {session_id}")
        print(f"Duplicate groups found: {len(groups)}")
        print(f"Total duplicate files: {total_files}")
        print()
        print(f"Use 'python cli.py list {session_id}' to view details")
        print(f"Use 'python cli.py export {session_id} --output results.csv' to export")
    finally:
        session.close()


def cmd_list(args):
    """List scan sessions or session details"""
    db = Database()
    session = db.get_session()

    try:
        if args.session_id:
            # Show details for specific session
            scan_session = session.query(ScanSession).filter_by(id=args.session_id).first()
            if not scan_session:
                print(f"Session {args.session_id} not found")
                sys.exit(1)

            print(f"Session {scan_session.id}: {scan_session.name}")
            print(f"Status: {scan_session.status}")
            print(f"Created: {scan_session.created_at}")
            print(f"Threshold: {scan_session.similarity_threshold * 100}%")
            print()

            groups = session.query(DuplicateGroup).filter_by(session_id=args.session_id).all()

            for i, group in enumerate(groups, 1):
                print(f"\nGroup {i} ({group.file_type}, {group.similarity_score*100:.1f}% similar):")
                print("-" * 50)
                for file_entry in group.files:
                    size_mb = file_entry.file_size / (1024 * 1024)
                    print(f"  {file_entry.file_path}")
                    print(f"    Size: {size_mb:.2f} MB")
        else:
            # List all sessions
            sessions = session.query(ScanSession).order_by(ScanSession.created_at.desc()).all()

            if not sessions:
                print("No scan sessions found")
                return

            print(f"{'ID':<6} {'Status':<12} {'Created':<20} {'Name'}")
            print("-" * 70)
            for s in sessions:
                created = s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else 'N/A'
                print(f"{s.id:<6} {s.status:<12} {created:<20} {s.name}")
    finally:
        session.close()


def cmd_export(args):
    """Export session results to CSV"""
    db = Database()
    session = db.get_session()

    try:
        scan_session = session.query(ScanSession).filter_by(id=args.session_id).first()
        if not scan_session:
            print(f"Session {args.session_id} not found")
            sys.exit(1)

        groups = session.query(DuplicateGroup).filter_by(session_id=args.session_id).all()

        with open(args.output, 'w') as f:
            # CSV header
            f.write("group_id,file_type,similarity,file_path,file_size_bytes,modified_time\n")

            for group in groups:
                for file_entry in group.files:
                    modified = file_entry.modified_time.isoformat() if file_entry.modified_time else ''
                    # Escape commas and quotes in file path
                    path = file_entry.file_path.replace('"', '""')
                    f.write(f'{group.id},{group.file_type},{group.similarity_score},"{path}",{file_entry.file_size},{modified}\n')

        total_files = sum(len(g.files) for g in groups)
        print(f"Exported {len(groups)} groups ({total_files} files) to {args.output}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='File Deduplicator CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py scan /path/to/folder --types image document
  python cli.py scan /path1 /path2 --types image --threshold 0.90
  python cli.py list
  python cli.py list 1
  python cli.py export 1 --output duplicates.csv
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan directories for duplicates')
    scan_parser.add_argument('paths', nargs='+', help='Paths to scan')
    scan_parser.add_argument('--types', '-t', nargs='+', default=['image', 'document'],
                            help='File types to scan (image, document, video, archive, code)')
    scan_parser.add_argument('--threshold', '-s', type=float, default=0.95,
                            help='Similarity threshold (0.0-1.0, default 0.95)')
    scan_parser.add_argument('--threads', type=int, default=4,
                            help='Number of threads (default 4)')
    scan_parser.add_argument('--recursive', '-r', action='store_true', default=True,
                            help='Include subdirectories (default: True)')
    scan_parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                            help='Do not include subdirectories')

    # List command
    list_parser = subparsers.add_parser('list', help='List scan sessions or session details')
    list_parser.add_argument('session_id', nargs='?', type=int, help='Session ID to show details')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export session results to CSV')
    export_parser.add_argument('session_id', type=int, help='Session ID to export')
    export_parser.add_argument('--output', '-o', default='duplicates.csv',
                              help='Output file path (default: duplicates.csv)')

    args = parser.parse_args()

    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'export':
        cmd_export(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
