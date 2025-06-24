import flet as ft
import asyncio
from login import login_page
from register import register_page
from setUpProficiency import set_up_proficiency_page, pretest_landing_page, pretest_score
from setUpTime import set_up_time_page
from mainmenu import main_menu_page
from levels import levels_page
from lesson import lesson_page
from chapterTest import chapter_test_page
from reviewFrame import daily_review_page
from wordLibrary import word_library_page
from settings import settings_page, about_page, acknowledgements_page
from achievements import achievement_page
from flet import Theme, PageTransitionsTheme, PageTransitionTheme

class CustomBKTPredictor:
    """Custom BKT predictor that directly uses the vocabulary parameters"""
    
    def __init__(self, vocab_parameters):
        """Initialize with vocabulary parameters"""
        self.vocab_parameters = vocab_parameters
    
    def predict(self, vocab, correct_history=None):
        """
        Predict knowledge state using BKT algorithm
        
        Parameters:
        - vocab: The vocabulary item to predict mastery for
        - correct_history: List of 1s and 0s representing correct/incorrect responses
                          (if None, returns prior probability)
        
        Returns:
        - Mastery probability (0-1)
        """
        if vocab not in self.vocab_parameters:
            return 0.5  # Default for unknown vocab
        
        params = self.vocab_parameters[vocab]
        learn = params.get('learn', 0.15)    # Learning probability
        guess = params.get('guess', 0.25)    # Guess probability
        slip = params.get('slip', 0.1)       # Slip probability
        prior = params.get('prior', 0.5)     # Prior probability of mastery
        
        # If no history provided, return prior
        if correct_history is None or len(correct_history) == 0:
            return prior
            
        # Start with prior probability
        mastery = prior
        
        # Update for each observation in history
        for is_correct in correct_history:
            # Step 1: Update based on observation
            if is_correct:
                # P(mastered | correct)
                mastery = (mastery * (1 - slip)) / (mastery * (1 - slip) + (1 - mastery) * guess)
            else:
                # P(mastered | incorrect)
                mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
                
            # Step 2: Account for learning
            mastery = mastery + (1 - mastery) * learn
            
        return mastery
    
    def predict_from_df(self, df):
        """
        Make predictions from a pandas DataFrame (similar to PyBKT interface)
        
        Parameters:
        - df: DataFrame with 'skill_name' and 'correct' columns
        
        Returns:
        - DataFrame with predictions added
        """
        result_df = df.copy()
        result_df['state_predictions'] = 0.0
        
        # Group by skill and user
        groups = df.groupby(['skill_name', 'user_id'])
        
        for (vocab, user), group in groups:
            # Get history of correct/incorrect for this user and skill
            history = group['correct'].astype(int).tolist()
            
            # Calculate probability for increasing prefixes of history
            for i in range(len(history)):
                prefix = history[:i+1]
                prob = self.predict(vocab, prefix)
                result_df.loc[group.index[i], 'state_predictions'] = prob
                
        return result_df
    
    def observe_with_scale(self, vocab, correct, impact_scale=1.0):
        """Observe a performance with scaled impact (for daily reviews)."""
        vocab = vocab.lower()  # Ensure lowercase for consistency
        
        if vocab not in self.vocab_parameters:
            self.vocab_parameters[vocab] = {
                'learn': 0.15,    # Default learning probability
                'guess': 0.25,    # Default guess probability
                'slip': 0.1,      # Default slip probability
                'prior': 0.5      # Default prior probability of mastery
            }
        
        # Get parameters for this vocabulary
        params = self.vocab_parameters[vocab]
        learn = params.get('learn', 0.15) * impact_scale  # Scale learning rate
        guess = params.get('guess', 0.25)
        slip = params.get('slip', 0.1)
        
        # Get current mastery
        mastery = params.get('prior', 0.5)
        
        # Update based on observation
        if correct:
            # P(mastered | correct)
            mastery = (mastery * (1 - slip)) / (mastery * (1 - slip) + (1 - mastery) * guess)
        else:
            # P(mastered | incorrect)
            mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
        
        # Apply scaled learning rate
        mastery = mastery + (1 - mastery) * learn
        
        # Update parameters
        params['prior'] = mastery  # Update prior for next observation
        self.vocab_parameters[vocab] = params
        
        print(f"[BKT] Vocab '{vocab}' mastery: {mastery:.2f} (scale: {impact_scale:.1f}, correct: {correct})")
        return mastery
    
    def mark_vocabulary_reviewed(self, vocab):
        """Mark a vocabulary as reviewed in daily review context"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            # Update the reviewed flag and timestamp
            self.vocab_parameters[vocab]['reviewed'] = True
            self.vocab_parameters[vocab]['last_reviewed'] = int(time.time())
            print(f"[BKT] Marked '{vocab}' as reviewed")
        else:
            # Initialize vocabulary if it doesn't exist
            import time
            self.vocab_parameters[vocab] = {
                'prior': 0.5,
                'guess': 0.25,
                'slip': 0.1,
                'learn': 0.15,
                'reviewed': True,
                'last_reviewed': int(time.time()),
                'observations': [],
                'response_times': []
            }
            print(f"[BKT] Initialized and marked '{vocab}' as reviewed")

    def get_mastery(self, vocab):
        """Get current mastery for a vocabulary"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            return float(self.vocab_parameters[vocab].get('prior', 0.5))
        return 0.5

    def is_reviewed(self, vocab):
        """Check if vocabulary has been reviewed"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            return self.vocab_parameters[vocab].get('reviewed', False)
        return False

    def get_vocabulary_in_order(self):
        """Get vocabulary ordered by mastery level (lowest first)"""
        if not self.vocab_parameters:
            return []  # Return empty list if no vocabulary
        
        # IMPORTANT: First populate order parameters if not present
        # This ensures new vocabularies get properly ordered
        for vocab in self.vocab_parameters.keys():
            if 'order' not in self.vocab_parameters[vocab]:
                # Assign a high order number to new vocabulary items
                self.vocab_parameters[vocab]['order'] = len(self.vocab_parameters) * 10
            
        # Try to sort by specified order parameter first
        try:
            sorted_vocab = sorted(
                self.vocab_parameters.keys(),
                key=lambda v: self.vocab_parameters[v].get('order', 999999)
            )
            return sorted_vocab
        except Exception as e:
            print(f"[BKT] Error sorting vocabulary by order: {e}")
            # Fall back to mastery-based sort
            try:
                sorted_vocab = sorted(
                    self.vocab_parameters.keys(),
                    key=lambda v: float(self.vocab_parameters[v].get('prior', 0.5))
                )
                return sorted_vocab
            except Exception as e:
                print(f"[BKT] Error sorting vocabulary: {e}")
                # Last resort - simple alphabetical sort
                return sorted(self.vocab_parameters.keys())

async def main(page: ft.Page):
    page.title = "User Authentication"
    page.bgcolor = "#FFFFFF"
    page.fonts = {
        "Poppins": "fonts/Poppins-Regular.ttf"
    }

    page.theme = ft.Theme(font_family="Poppins", 
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.OPEN_UPWARDS,
            ios=ft.PageTransitionTheme.CUPERTINO,
            macos=ft.PageTransitionTheme.FADE_UPWARDS,
            windows=ft.PageTransitionTheme.FADE_UPWARDS
        )
    )

    image_urls = [
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747639160/logo1_tkfwwq.png", #blue logo - 0
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747639363/logo_roygvs.png", #purple logo - 1
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/kamustahayPic_l8q9m7.jpg", #kamustahay card - 2
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/kalakatPic_lhx9x8.jpg", #kalakat - 3
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/pamalitPic_wufwce.png", #pamalit - 4
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642328/pangaonPic_tuterr.png", #pangaon - 5
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653515/urusturyaPic_uio1qv.png", #urusturya - 6
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653929/aga_zbtuat.jpg", #my progress photo - 7
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653842/landscape_background_vppv58.png", #landscape background - 8
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653843/reviewPic_kxjqm3.png", #review card - 9


    ]

    # Preload images in a hidden container
    preload_container = ft.Column(
        controls=[ft.Image(src=url, visible=False) for url in image_urls]
    )

    page.add(preload_container)

    # Splash screen function
    async def show_splash_screen():

        page.controls.clear()
        
        splash_image = ft.Image(
            src=image_urls[0],  # Use the first image URL
            width=180,
            height=180,
            fit=ft.ImageFit.CONTAIN
        )
        
        # Loading indicator (optional)
        progress_ring = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            color="#4285F4"
        )
        
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        splash_image,
                        ft.Container(height=5),  # Spacing
                        progress_ring
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor="white"  # White bg
            )
        )
        
        page.update()
        
        await asyncio.sleep(4)
        page.go("/login")

    def route_change(e):
        """Handles route changes to switch between pages."""
        page.views.clear()

        if page.route == "/register":
            register_page(page, image_urls)
        elif page.route == "/setup-proficiency":
            set_up_proficiency_page(page, image_urls)
        elif page.route == "/setup-time":
            set_up_time_page(page, image_urls)
        elif page.route == "/main-menu":
            main_menu_page(page, image_urls)
        elif page.route == "/levels":
            levels_page(page, image_urls)
        elif page.route == "/lesson":
            lesson_page(page, image_urls)
        elif page.route == "/chaptertest":
            chapter_test_page(page, image_urls)
        elif page.route == "/daily-review":
            daily_review_page(page, image_urls)
        elif page.route == "/word-library":
            word_library_page(page, image_urls)
        elif page.route == "/settings":
            settings_page(page)
        elif page.route == "/about":
            about_page(page, image_urls)
        elif page.route == "/acknowledgements":
            acknowledgements_page(page)
        elif page.route == "/achievements":
            achievement_page(page, image_urls)
        elif page.route == "/pretest-intro":
            pretest_landing_page(page, image_urls)
        elif page.route == "/pretest-score":
            pretest_score(page, image_urls)
        else:
            login_page(page, image_urls)  # Default to login page

        page.update()

    page.on_route_change = route_change
    await show_splash_screen()

ft.app(target=main)