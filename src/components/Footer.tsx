export const Footer = () => {
  return (
    <footer className="border-t border-border/50 bg-muted/30 mt-16 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-chart-2 rounded-lg flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M3 17L9 11L13 15L21 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M14 7H21V14" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">Rife-Trade</p>
              <p className="text-xs text-muted-foreground">© 2025 All rights reserved</p>
            </div>
          </div>
          
          <nav className="flex items-center gap-8 text-sm">
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 font-medium">
              About
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 font-medium">
              Privacy
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 font-medium">
              Terms
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 font-medium">
              Contact
            </a>
          </nav>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-accent/50 px-3 py-2 rounded-lg border border-primary/20">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            <span className="font-medium">Auto-refresh: 60s</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
