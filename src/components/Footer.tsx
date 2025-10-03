export const Footer = () => {
  return (
    <footer className="border-t-2 border-primary/20 bg-gradient-to-r from-primary/5 to-chart-5/5 mt-12 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm font-medium text-foreground">
            © 2025 Rife-Trade. All rights reserved.
          </div>
          <div className="flex items-center gap-6 text-sm">
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors font-medium">
              About
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors font-medium">
              Privacy
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors font-medium">
              Terms
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors font-medium">
              Contact
            </a>
          </div>
          <div className="text-sm font-medium text-foreground bg-card px-4 py-2 rounded-lg border-2 border-primary/20">
            Auto-refresh: 60s
          </div>
        </div>
      </div>
    </footer>
  );
};
