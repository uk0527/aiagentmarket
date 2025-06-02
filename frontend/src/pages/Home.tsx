import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Button,
  Box
} from '@mui/material';
import Grid from '@mui/material/Grid';

interface FeaturedAgent {
  id: number;
  name: string;
  description: string;
  price: number;
  image: string;
  rating: number;
}

const featuredAgents: FeaturedAgent[] = [
  {
    id: 1,
    name: 'Portfolio Analysis Agent',
    description: 'AI-powered portfolio analysis and optimization',
    price: 99.99,
    image: 'https://via.placeholder.com/300',
    rating: 4.5
  },
  {
    id: 2,
    name: 'Trading Strategy Agent',
    description: 'Automated trading strategy generation',
    price: 149.99,
    image: 'https://via.placeholder.com/300',
    rating: 4.8
  },
  {
    id: 3,
    name: 'Market Research Agent',
    description: 'Real-time market research and analysis',
    price: 199.99,
    image: 'https://via.placeholder.com/300',
    rating: 4.7
  }
];

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Welcome to AI Agent Marketplace
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Discover and deploy powerful AI agents for your business needs
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/agents')}
          sx={{ mt: 2 }}
        >
          Browse All Agents
        </Button>
      </Box>

      <Typography variant="h4" component="h2" gutterBottom sx={{ mb: 4 }}>
        Featured Agents
      </Typography>

      <Grid container spacing={4}>
        {featuredAgents.map((agent) => (
          <Grid item xs={12} sm={6} md={4} key={agent.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  transition: 'transform 0.2s ease-in-out'
                }
              }}
            >
              <CardMedia
                component="img"
                height="200"
                image={agent.image}
                alt={agent.name}
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5" component="h2">
                  {agent.name}
                </Typography>
                <Typography color="text.secondary" paragraph>
                  {agent.description}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" color="primary">
                    ${agent.price}
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(`/agents/${agent.id}`)}
                  >
                    Learn More
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Home; 