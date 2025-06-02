import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  IconButton,
  Alert
} from '@mui/material';
import Grid from '@mui/material/Grid';
import DeleteIcon from '@mui/icons-material/Delete';
import { useCart } from '../contexts/CartContext';
import LoadingSpinner from '../components/LoadingSpinner';

const AgentCart: React.FC = () => {
  const { items, loading, error, removeFromCart, checkout } = useCart();

  const handleCheckout = async () => {
    try {
      await checkout();
      // Handle successful checkout (e.g., show success message, redirect)
    } catch (err) {
      // Error is already handled in the context
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (items.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Your Cart is Empty
        </Typography>
        <Typography color="text.secondary">
          Add some AI agents to your cart to get started.
        </Typography>
      </Container>
    );
  }

  const total = items.reduce((sum, item) => sum + item.price, 0);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Your Cart
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          {items.map((item) => (
            <Card key={item.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h6" component="h2">
                      {item.name}
                    </Typography>
                    <Typography color="text.secondary">
                      {item.description}
                    </Typography>
                    <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
                      ${item.price}
                    </Typography>
                  </Box>
                  <IconButton
                    color="error"
                    onClick={() => removeFromCart(item.id)}
                    aria-label="remove from cart"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Order Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Subtotal</Typography>
                <Typography>${total.toFixed(2)}</Typography>
              </Box>
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleCheckout}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Proceed to Checkout'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AgentCart; 