import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';

@Component({
    selector: 'app-temp',
    standalone: true,
    imports: [CommonModule, ButtonModule],
    templateUrl: './temp.html',
    styleUrls: ['./temp.css']
})
export class TempComponent implements OnInit {
    randomQuotes: string[] = [
        '🚀 Did you know? This is a temporary help page!',
        '💡 Feature under development - Check back soon!',
        '🎯 Help content coming to this section',
        '✨ This section is being prepared for you',
        '🔧 Detailed help documentation will appear here',
        '📚 In-app help and guidance center',
        '❓ Your questions answered here soon',
        '🛠️ Configuration guide and best practices',
        '📖 Complete documentation and tutorials',
        '🎓 Learn more about this feature'
    ];

    randomEmojis: string[] = ['🎨', '🎭', '🎪', '🎬', '🎤', '🎧', '🎯', '🎲', '🎮', '🎸'];
    
    selectedQuote: string = '';
    selectedEmoji: string = '';

    constructor(private router: Router) {}

    ngOnInit() {
        this.selectRandomQuote();
        this.selectRandomEmoji();
    }

    selectRandomQuote() {
        const randomIndex = Math.floor(Math.random() * this.randomQuotes.length);
        this.selectedQuote = this.randomQuotes[randomIndex];
    }

    selectRandomEmoji() {
        const randomIndex = Math.floor(Math.random() * this.randomEmojis.length);
        this.selectedEmoji = this.randomEmojis[randomIndex];
    }

    goBack() {
        this.router.navigate(['/home']);
    }
}
