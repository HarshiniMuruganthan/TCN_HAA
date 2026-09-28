import tensorflow as tf
from tensorflow.keras.layers import Layer


@tf.keras.utils.register_keras_serializable(package="custom_layers")
class HealthAwareAttention(Layer):
    """
    Health-Aware Attention (HAA) Layer for Temporal Convolutional Networks.

    Mechanism:
    ----------
    Given temporal features H in R^(B x T x D) from dilated causal Conv1D blocks:
    1. Score projection: e_t = tanh(H · W_a + b_a)
    2. Context alignment with learnable health context vector u_h:
       s_t = e_t · u_h
    3. Attention distribution over time steps:
       alpha = softmax(s_t, axis=1)  # shape: (B, T, 1)
    4. Attended context representation:
       c = sum_t (alpha_t * h_t)     # shape: (B, D)

    Parameters:
    -----------
    return_attention : bool, default=False
        If True, call() returns (context_vector, attention_weights).
        If False, call() returns only context_vector.
    """

    def __init__(self, return_attention: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.return_attention = return_attention

    def build(self, input_shape):
        feature_dim = input_shape[-1]

        # Projection weights W_a
        self.W_a = self.add_weight(
            name="attention_weight",
            shape=(feature_dim, feature_dim),
            initializer="glorot_uniform",
            trainable=True,
        )

        # Projection bias b_a
        self.b_a = self.add_weight(
            name="attention_bias",
            shape=(feature_dim,),
            initializer="zeros",
            trainable=True,
        )

        # Health context scoring vector u_h (initialized to zeros for smooth warm-start from uniform pooling)
        self.u_h = self.add_weight(
            name="health_context_vector",
            shape=(feature_dim, 1),
            initializer="zeros",
            trainable=True,
        )

        super().build(input_shape)

    def call(self, inputs, **kwargs):
        # inputs shape: (batch_size, time_steps, feature_dim)
        # 1. Project temporal features: (B, T, D) -> (B, T, D)
        score_proj = tf.tanh(tf.tensordot(inputs, self.W_a, axes=[[2], [0]]) + self.b_a)

        # 2. Alignment with health context vector: (B, T, D) x (D, 1) -> (B, T, 1)
        scores = tf.tensordot(score_proj, self.u_h, axes=[[2], [0]])

        # 3. Normalized attention distribution across sequence length
        attention_weights = tf.nn.softmax(scores, axis=1)

        # 4. Compute attended context vector: (B, T, D) * (B, T, 1) -> sum along T -> (B, D)
        context_vector = tf.reduce_sum(inputs * attention_weights, axis=1)

        if self.return_attention:
            return context_vector, attention_weights
        return context_vector

    def compute_output_shape(self, input_shape):
        batch_size = input_shape[0]
        feature_dim = input_shape[-1]
        if self.return_attention:
            time_steps = input_shape[1]
            return [(batch_size, feature_dim), (batch_size, time_steps, 1)]
        return (batch_size, feature_dim)

    def get_config(self):
        config = super().get_config()
        config.update({"return_attention": self.return_attention})
        return config
