# remove_stories_direct.py
import psycopg2
import sys
from decouple import config

def remove_stories():
    try:
        print("🔄 Connecting to RDS...")
        
        # Connect using your environment variables
        conn = psycopg2.connect(
            host=config('DB_HOST', default='connectify-database.c7gyoua607m0.eu-north-1.rds.amazonaws.com'),
            port=config('DB_PORT', default='5432'),
            database=config('DB_NAME', default='connectify_aws'),
            user=config('DB_USER', default='postgres'),
            password=config('DB_PASSWORD', default='N4qhtnqd123'),
            connect_timeout=60
        )
        
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        print("🔄 Checking existing tables...")
        
        # Check if story tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('stories', 'story_views');
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found story tables: {existing_tables}")
        
        if existing_tables:
            print("🗑️ Removing story tables...")
            
            # Drop story tables safely
            cursor.execute("DROP TABLE IF EXISTS story_views CASCADE;")
            print("   ✅ Dropped story_views table")
            
            cursor.execute("DROP TABLE IF EXISTS stories CASCADE;")
            print("   ✅ Dropped stories table")
            
            # Commit changes
            conn.commit()
            print("✅ Story tables removed successfully!")
        else:
            print("ℹ️ No story tables found - already removed or never existed")
        
        # Close connection
        cursor.close()
        conn.close()
        print("✅ Connection closed")
        
        return True
        
    except psycopg2.OperationalError as e:
        if "timeout" in str(e).lower():
            print("❌ Connection timeout - try again or check your network")
        else:
            print(f"❌ Database connection error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = remove_stories()
    
    if success:
        print("\n🎉 Story removal completed!")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate --fake core 0003")
        print("2. Run: python manage.py runserver")
    else:
        print("\n💡 If connection keeps failing, try:")
        print("1. Different network (mobile hotspot)")
        print("2. VPN to different location")
        print("3. AWS CloudShell from AWS Console")
        sys.exit(1)