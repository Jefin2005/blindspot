"""
Management command to seed the database with sample data for Cochin/Kochi
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from core.models import Authority, Category, Issue, IssueConfirmation, UserProfile


class Command(BaseCommand):
    help = 'Seeds the database with sample civic issues for Cochin'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create authorities
        authorities_data = [
            {
                'name': 'Water Authority',
                'description': 'Kerala Water Authority - Responsible for water supply and drainage',
                'icon': 'fa-droplet',
                'color': '#06b6d4'
            },
            {
                'name': 'Municipal Corporation',
                'description': 'Kochi Municipal Corporation - Waste management and sanitation',
                'icon': 'fa-building-columns',
                'color': '#8b5cf6'
            },
            {
                'name': 'Electricity Board',
                'description': 'KSEB - Kerala State Electricity Board',
                'icon': 'fa-bolt',
                'color': '#fbbf24'
            },
            {
                'name': 'Urban Infrastructure',
                'description': 'Roads, bridges, walkways, and public spaces',
                'icon': 'fa-road',
                'color': '#f97316'
            },
        ]
        
        authorities = {}
        for data in authorities_data:
            auth, created = Authority.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            authorities[data['name']] = auth
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"  Authority: {data['name']} - {status}")
        
        # Create categories
        categories_data = [
            # Water Authority
            {'authority': 'Water Authority', 'name': 'Water Leakage', 'icon': 'fa-droplet', 'default_severity': 4},
            {'authority': 'Water Authority', 'name': 'Pipeline Burst', 'icon': 'fa-burst', 'default_severity': 5},
            {'authority': 'Water Authority', 'name': 'Open Drain', 'icon': 'fa-water', 'default_severity': 4},
            {'authority': 'Water Authority', 'name': 'Sewage Overflow', 'icon': 'fa-poo', 'default_severity': 5},
            
            # Municipal Corporation
            {'authority': 'Municipal Corporation', 'name': 'Waste Dumping', 'icon': 'fa-trash', 'default_severity': 4},
            {'authority': 'Municipal Corporation', 'name': 'Overflowing Bins', 'icon': 'fa-dumpster', 'default_severity': 3},
            {'authority': 'Municipal Corporation', 'name': 'Poor Sanitation', 'icon': 'fa-broom', 'default_severity': 3},
            {'authority': 'Municipal Corporation', 'name': 'Stray Animal Menace', 'icon': 'fa-dog', 'default_severity': 3},
            
            # Electricity Board
            {'authority': 'Electricity Board', 'name': 'Broken Streetlight', 'icon': 'fa-lightbulb', 'default_severity': 3},
            {'authority': 'Electricity Board', 'name': 'Exposed Wires', 'icon': 'fa-plug', 'default_severity': 5},
            {'authority': 'Electricity Board', 'name': 'Fallen Electric Pole', 'icon': 'fa-plug-circle-exclamation', 'default_severity': 5},
            {'authority': 'Electricity Board', 'name': 'Transformer Issue', 'icon': 'fa-car-battery', 'default_severity': 4},
            
            # Urban Infrastructure
            {'authority': 'Urban Infrastructure', 'name': 'Pothole', 'icon': 'fa-circle-exclamation', 'default_severity': 4},
            {'authority': 'Urban Infrastructure', 'name': 'Damaged Walkway', 'icon': 'fa-person-walking', 'default_severity': 3},
            {'authority': 'Urban Infrastructure', 'name': 'Broken Footbridge', 'icon': 'fa-bridge', 'default_severity': 4},
            {'authority': 'Urban Infrastructure', 'name': 'Unsafe Public Space', 'icon': 'fa-triangle-exclamation', 'default_severity': 4},
        ]
        
        categories = {}
        for data in categories_data:
            cat, created = Category.objects.get_or_create(
                authority=authorities[data['authority']],
                name=data['name'],
                defaults={
                    'icon': data['icon'],
                    'default_severity': data['default_severity']
                }
            )
            categories[data['name']] = cat
        
        self.stdout.write(f"  Created {len(categories_data)} categories")
        
        # Create a demo user if not exists
        demo_user, created = User.objects.get_or_create(
            username='citizen',
            defaults={
                'email': 'citizen@blindspot.local',
                'is_active': True
            }
        )
        if created:
            demo_user.set_password('watchdog123')
            demo_user.save()
            UserProfile.objects.create(user=demo_user, area='Kochi')
            self.stdout.write('  Created demo user: citizen / watchdog123')
        
        # Cochin/Kochi locations with realistic issue data
        issues_data = [
            # Marine Drive area
            {
                'title': 'Major water pipeline burst near Marine Drive',
                'description': 'A large water pipeline has burst near the Marine Drive walkway, causing flooding and water wastage. The area has become slippery and dangerous for pedestrians.',
                'category': 'Pipeline Burst',
                'latitude': 9.9815,
                'longitude': 76.2760,
                'address': 'Marine Drive, Near Subhash Bose Park',
                'severity': 5,
                'days_ago': 45
            },
            {
                'title': 'Multiple streetlights not working along Marine Drive',
                'description': 'At least 8 streetlights are not functioning along the Marine Drive stretch. The area becomes dangerously dark after sunset.',
                'category': 'Broken Streetlight',
                'latitude': 9.9789,
                'longitude': 76.2745,
                'address': 'Marine Drive, Kochi',
                'severity': 4,
                'days_ago': 28
            },
            
            # MG Road area
            {
                'title': 'Large pothole causing accidents near MG Road junction',
                'description': 'A dangerous pothole has formed at the MG Road - SA Road junction. Multiple two-wheeler accidents reported. Temporary fix has washed away.',
                'category': 'Pothole',
                'latitude': 9.9686,
                'longitude': 76.2848,
                'address': 'MG Road Junction, Near Jose Junction',
                'severity': 5,
                'days_ago': 52
            },
            {
                'title': 'Garbage dump near MG Road Metro station',
                'description': 'Illegal garbage dumping behind the metro station. Foul smell affecting nearby businesses. No regular collection.',
                'category': 'Waste Dumping',
                'latitude': 9.9712,
                'longitude': 76.2891,
                'address': 'Behind MG Road Metro Station',
                'severity': 4,
                'days_ago': 18
            },
            
            # Fort Kochi
            {
                'title': 'Sewage overflow near Chinese Fishing Nets',
                'description': 'Sewage is overflowing onto the tourist area near the famous Chinese Fishing Nets. Health hazard and embarrassment for tourists.',
                'category': 'Sewage Overflow',
                'latitude': 9.9658,
                'longitude': 76.2424,
                'address': 'Fort Kochi Beach, Near Chinese Fishing Nets',
                'severity': 5,
                'days_ago': 35
            },
            {
                'title': 'Damaged heritage walkway in Fort Kochi',
                'description': 'The cobblestone walkway near St. Francis Church is badly damaged. Uneven stones causing trip hazards for elderly tourists.',
                'category': 'Damaged Walkway',
                'latitude': 9.9636,
                'longitude': 76.2436,
                'address': 'Church Road, Fort Kochi',
                'severity': 3,
                'days_ago': 67
            },
            
            # Ernakulam North
            {
                'title': 'Exposed electric wires on Banerji Road',
                'description': 'Dangerous exposed wires hanging low near a school. Children at risk. Reported multiple times with no action.',
                'category': 'Exposed Wires',
                'latitude': 9.9892,
                'longitude': 76.2831,
                'address': 'Banerji Road, Near St. Teresas School',
                'severity': 5,
                'days_ago': 22
            },
            {
                'title': 'Overflowing garbage bins at Kaloor',
                'description': 'The community bins at Kaloor junction have been overflowing for over a week. Crows and stray dogs spreading garbage.',
                'category': 'Overflowing Bins',
                'latitude': 9.9910,
                'longitude': 76.3047,
                'address': 'Kaloor Junction, Stadium Link Road',
                'severity': 3,
                'days_ago': 12
            },
            
            # Edappally area
            {
                'title': 'Massive open drain near Lulu Mall',
                'description': 'An open drain near the Lulu Mall service road is uncovered and poses serious risk. Children playing nearby.',
                'category': 'Open Drain',
                'latitude': 10.0261,
                'longitude': 76.3084,
                'address': 'Edappally, Near Lulu Mall Service Road',
                'severity': 4,
                'days_ago': 31
            },
            {
                'title': 'Street light pole damaged by accident',
                'description': 'A vehicle accident damaged the street light pole 2 weeks ago. The pole is leaning dangerously and may fall.',
                'category': 'Fallen Electric Pole',
                'latitude': 10.0245,
                'longitude': 76.3102,
                'address': 'Edappally Toll Junction',
                'severity': 5,
                'days_ago': 14
            },
            
            # Kakkanad
            {
                'title': 'Poor road conditions near Infopark',
                'description': 'The access road to Infopark Phase 2 has multiple potholes and broken edges. Daily commuters suffering.',
                'category': 'Pothole',
                'latitude': 10.0084,
                'longitude': 76.3573,
                'address': 'Infopark Road, Kakkanad',
                'severity': 4,
                'days_ago': 40
            },
            {
                'title': 'Stray dog menace near CSEZ',
                'description': 'Pack of aggressive stray dogs near the CSEZ gate. Multiple reports of chasing incidents with IT employees.',
                'category': 'Stray Animal Menace',
                'latitude': 10.0156,
                'longitude': 76.3614,
                'address': 'CSEZ Gate, Kakkanad',
                'severity': 4,
                'days_ago': 25
            },
            
            # Vyttila
            {
                'title': 'Water leakage at Vyttila Hub',
                'description': 'Major water leakage from underground pipe at the mobility hub. Water pooling on the road causing traffic issues.',
                'category': 'Water Leakage',
                'latitude': 9.9673,
                'longitude': 76.3203,
                'address': 'Vyttila Mobility Hub',
                'severity': 4,
                'days_ago': 8
            },
            {
                'title': 'Broken footbridge at Vyttila junction',
                'description': 'The pedestrian footbridge has broken railings and slippery surface. Very unsafe during monsoon.',
                'category': 'Broken Footbridge',
                'latitude': 9.9685,
                'longitude': 76.3187,
                'address': 'Vyttila Junction Footbridge',
                'severity': 4,
                'days_ago': 55
            },
            
            # Thevara
            {
                'title': 'Illegal dumping ground near Thevara Ferry',
                'description': 'People dumping construction debris and household waste near the ferry terminal. Blocking pathway to boats.',
                'category': 'Waste Dumping',
                'latitude': 9.9494,
                'longitude': 76.2927,
                'address': 'Thevara Ferry Terminal',
                'severity': 3,
                'days_ago': 19
            },
            {
                'title': 'Transformer sparking frequently',
                'description': 'The transformer near Thevara junction sparks every time it rains. Residents living in fear of fire.',
                'category': 'Transformer Issue',
                'latitude': 9.9518,
                'longitude': 76.2965,
                'address': 'Thevara Junction',
                'severity': 5,
                'days_ago': 33
            },
            
            # Palarivattom
            {
                'title': 'Dangerous pothole on flyover',
                'description': 'A pothole has formed on the Palarivattom flyover surface. Vehicles swerving to avoid it causing near-accidents.',
                'category': 'Pothole',
                'latitude': 9.9945,
                'longitude': 76.3058,
                'address': 'Palarivattom Flyover',
                'severity': 5,
                'days_ago': 6
            },
            {
                'title': 'Multiple streetlights out near bypass',
                'description': 'About 500m stretch of the bypass road near Palarivattom has no working streetlights. Theft incidents reported.',
                'category': 'Broken Streetlight',
                'latitude': 9.9962,
                'longitude': 76.3089,
                'address': 'Seaport-Airport Road, Palarivattom',
                'severity': 4,
                'days_ago': 47
            },
            
            # Aluva
            {
                'title': 'Sewage mixing with river near Aluva',
                'description': 'Untreated sewage directly flowing into Periyar river near Aluva bridge. Environmental disaster.',
                'category': 'Sewage Overflow',
                'latitude': 10.1076,
                'longitude': 76.3523,
                'address': 'Aluva Bridge, Periyar River',
                'severity': 5,
                'days_ago': 62
            },
            {
                'title': 'Unsafe public park near Aluva Palace',
                'description': 'Broken benches, scattered glass, and poor lighting making the heritage park unusable after dark.',
                'category': 'Unsafe Public Space',
                'latitude': 10.1054,
                'longitude': 76.3498,
                'address': 'Aluva Palace Ground',
                'severity': 3,
                'days_ago': 29
            },
            
            # Tripunithura
            {
                'title': 'Open drain near Hill Palace',
                'description': 'Storm water drain near the famous Hill Palace Museum is completely open. Tourist safety concern.',
                'category': 'Open Drain',
                'latitude': 9.9486,
                'longitude': 76.3507,
                'address': 'Hill Palace Road, Tripunithura',
                'severity': 4,
                'days_ago': 38
            },
            
            # Mattancherry
            {
                'title': 'Heritage area sanitation neglect',
                'description': 'The Jew Town heritage area has poor sanitation. Garbage piling up near antique shops.',
                'category': 'Poor Sanitation',
                'latitude': 9.9578,
                'longitude': 76.2596,
                'address': 'Jew Town, Mattancherry',
                'severity': 4,
                'days_ago': 44
            },
            {
                'title': 'Damaged walkway near Mattancherry Palace',
                'description': 'The walkway leading to the Dutch Palace has broken tiles and uneven surfaces.',
                'category': 'Damaged Walkway',
                'latitude': 9.9584,
                'longitude': 76.2602,
                'address': 'Mattancherry Palace Road',
                'severity': 3,
                'days_ago': 51
            },
            
            # Willingdon Island
            {
                'title': 'Water main leak near port area',
                'description': 'Large water main leaking for weeks near the Cochin Port area. Significant water wastage.',
                'category': 'Water Leakage',
                'latitude': 9.9622,
                'longitude': 76.2678,
                'address': 'Willingdon Island, Port Area',
                'severity': 4,
                'days_ago': 23
            },
            
            # Panampilly Nagar
            {
                'title': 'Overflowing garbage at residential area',
                'description': 'The designated garbage collection point in Panampilly Nagar is overflowing onto the road.',
                'category': 'Overflowing Bins',
                'latitude': 9.9578,
                'longitude': 76.3024,
                'address': 'Panampilly Nagar, Near Aster Medcity',
                'severity': 3,
                'days_ago': 7
            },
        ]
        
        # Create issues
        now = timezone.now()
        created_count = 0
        
        for data in issues_data:
            reported_at = now - timedelta(days=data['days_ago'])
            
            # Randomly set some as acknowledged or resolved
            status = 'ignored'
            acknowledged_at = None
            resolved_at = None
            
            rand = random.random()
            if rand > 0.85:
                status = 'resolved'
                acknowledged_at = reported_at + timedelta(days=random.randint(1, data['days_ago']//2))
                resolved_at = now - timedelta(days=random.randint(1, 5))
            elif rand > 0.7:
                status = 'acknowledged'
                acknowledged_at = reported_at + timedelta(days=random.randint(1, min(10, data['days_ago'])))
            
            issue, created = Issue.objects.get_or_create(
                title=data['title'],
                defaults={
                    'description': data['description'],
                    'category': categories[data['category']],
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'address': data['address'],
                    'severity': data['severity'],
                    'status': status,
                    'reported_at': reported_at,
                    'acknowledged_at': acknowledged_at,
                    'resolved_at': resolved_at,
                    'reported_by': demo_user
                }
            )
            
            if created:
                created_count += 1
                # Add random confirmations
                num_confirmations = random.randint(3, 30)
                # We'll just set a count without actual users for demo
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} issues'))
        self.stdout.write(self.style.SUCCESS('Database seeding complete!'))
        self.stdout.write('')
        self.stdout.write('Demo credentials:')
        self.stdout.write('  Username: citizen')
        self.stdout.write('  Password: watchdog123')
