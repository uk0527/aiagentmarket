import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Button,
  Box,
  IconButton,
  Divider,
  Paper,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { useCart } from '../contexts/CartContext';
import LoadingSpinner from '../components/LoadingSpinner';

const AgentCart = () => {
  const navigate = useNavigate();
  const { items, loading, error, removeFromCart, checkout } = useCart();

  const handleRemoveItem = async (agentId) => {
    try {
      await removeFromCart(agentId);
    } catch (err) {
      // Error is handled by the cart context
    }
  };

  const handleCheckout = async () => {
    try {
      await checkout();
      navigate('/purchases');
    } catch (err) {
      // Error is handled by the cart context
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  const total = items.reduce((sum, item) => sum + item.price, 0);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Shopping Cart
      </Typography>
      
      {items.length === 0 ? (
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Your cart is empty
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/agents')}
            sx={{ mt: 2 }}
          >
            Browse Agents
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {items.map((item) => (
              <Card key={item.id} sx={{ mb: 2 }}>
                <CardContent>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <CardMedia
                        component="img"
                        height="140"
                        image={item.image}
                        alt={item.name}
                      />
                    </Grid>
                    <Grid item xs={12} sm={7}>
                      <Typography variant="h6">{item.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {item.description}
                      </Typography>
                      <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
                        ${item.price}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={2}>
                      <IconButton
                        color="error"
                        onClick={() => handleRemoveItem(item.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            ))}
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Order Summary
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Subtotal</Typography>
                <Typography>${total.toFixed(2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Tax</Typography>
                <Typography>${(total * 0.1).toFixed(2)}</Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Total</Typography>
                <Typography variant="h6">${(total * 1.1).toFixed(2)}</Typography>
              </Box>
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleCheckout}
              >
                Proceed to Checkout
              </Button>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default AgentCart; 